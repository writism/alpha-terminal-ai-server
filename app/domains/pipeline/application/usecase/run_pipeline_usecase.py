import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Awaitable, Callable, Optional

from app.domains.pipeline.application.request.run_pipeline_request import ArticleMode
from app.domains.pipeline.application.response.analysis_log_response import AnalysisLogResponse
from app.domains.pipeline.application.response.stock_summary_response import StockSummaryResponse
from app.domains.stock_analyzer.application.usecase.article_analyzer_port import ArticleAnalyzerPort
from app.domains.stock_analyzer.application.usecase.get_or_create_analysis_usecase import GetOrCreateAnalysisUseCase
from app.domains.stock_collector.application.usecase.collect_articles_usecase import CollectArticlesUseCase
from app.domains.stock_normalizer.application.request.normalize_raw_article_request import NormalizeRawArticleRequest
from app.domains.stock_normalizer.application.usecase.normalize_raw_article_usecase import NormalizeRawArticleUseCase

logger = logging.getLogger(__name__)

NEWS_SOURCE_TYPES = {"NEWS"}
REPORT_SOURCE_TYPES = {"DISCLOSURE", "REPORT"}

OnEvent = Callable[[dict], Awaitable[None]]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


async def _emit(on_event: Optional[OnEvent], event: dict) -> None:
    if on_event:
        await on_event(event)


_PUBLISHED_AT_FORMATS = [
    "%m/%d/%Y, %I:%M %p, +0000 UTC",   # 07/31/2019, 08:16 PM, +0000 UTC  (Finnhub/News)
    "%Y%m%d",                           # 20260330  (DART)
    "%Y-%m-%dT%H:%M:%S",               # ISO without tz
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d",
]


def _get_published_dt(raw) -> datetime:
    s = str(raw.published_at).strip() if raw.published_at else ""
    if not s:
        return datetime.min
    # fromisoformat 먼저 시도 (timezone-aware 포함)
    try:
        dt = datetime.fromisoformat(s)
        return dt.replace(tzinfo=None) if dt.tzinfo else dt
    except ValueError:
        pass
    # 알려진 포맷 순차 시도
    for fmt in _PUBLISHED_AT_FORMATS:
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return datetime.min


def _select_articles(articles: list, mode: ArticleMode) -> list:
    """최신순 정렬 후 mode에 따라 기사 선택."""
    sorted_arts = sorted(articles, key=_get_published_dt, reverse=True)
    if mode == ArticleMode.LATEST_1:
        return sorted_arts[:1]
    elif mode == ArticleMode.LATEST_3:
        return sorted_arts[:3]
    elif mode == ArticleMode.LATEST_5:
        return sorted_arts[:5]
    elif mode == ArticleMode.LAST_24H:
        cutoff = datetime.now() - timedelta(hours=24)
        filtered = [a for a in sorted_arts if _get_published_dt(a) >= cutoff]
        return filtered if filtered else sorted_arts[:1]
    return sorted_arts[:3]


class RunPipelineUseCase:
    def __init__(
        self,
        watchlist_repository,
        raw_article_repository,
        collectors: list,
        normalize_usecase: NormalizeRawArticleUseCase,
        analysis_usecase: GetOrCreateAnalysisUseCase,
        on_progress=None,
        stock_repository=None,
        analyzer_port: Optional[ArticleAnalyzerPort] = None,
    ):
        self._watchlist_repository = watchlist_repository
        self._raw_article_repository = raw_article_repository
        self._collectors = collectors
        self._normalize_usecase = normalize_usecase
        self._analysis_usecase = analysis_usecase
        self._stock_repository = stock_repository
        self._analyzer_port = analyzer_port

    async def execute(
        self,
        selected_symbols: Optional[list[str]] = None,
        account_id: Optional[int] = None,
        on_event: Optional[OnEvent] = None,
        article_mode: ArticleMode = ArticleMode.LATEST_3,
    ) -> dict:
        watchlist_items = self._watchlist_repository.find_all(account_id=account_id)
        if not watchlist_items:
            return {"message": "관심종목이 없습니다.", "processed": [], "summaries": [], "report_summaries": [], "logs": []}

        if selected_symbols:
            selected_set = {symbol.upper() for symbol in selected_symbols}
            watchlist_items = [item for item in watchlist_items if item.symbol.upper() in selected_set]
            if not watchlist_items:
                return {"message": "선택한 관심종목이 없습니다.", "processed": [], "summaries": [], "report_summaries": [], "logs": []}

        total = len(watchlist_items)
        await _emit(on_event, {
            "type": "progress",
            "phase": "START",
            "at": _now(),
            "message": f"관심종목 {total}개 파이프라인 시작",
        })

        # Phase 1: 수집 (순차 — DB 세션 공유)
        no_article_symbols = []
        symbol_data: dict[str, tuple] = {}  # symbol → (name, news_articles, report_articles)

        for idx, item in enumerate(watchlist_items, 1):
            symbol = item.symbol
            name = item.name
            await _emit(on_event, {
                "type": "progress",
                "phase": "COLLECT",
                "symbol": symbol,
                "at": _now(),
                "message": f"[{idx}/{total}] {name}({symbol}) 기사 수집 중...",
                "progress": {"current": idx, "total": total},
            })
            try:
                collect_usecase = CollectArticlesUseCase(self._raw_article_repository, self._collectors, self._stock_repository)
                await asyncio.to_thread(collect_usecase.execute, symbol)
            except Exception as e:
                logger.error(f"[Pipeline] {name}({symbol}) 수집 중 오류: {e}")
                await _emit(on_event, {
                    "type": "error",
                    "phase": "COLLECT",
                    "symbol": symbol,
                    "at": _now(),
                    "message": f"[{idx}/{total}] {name}({symbol}) 수집 오류 — 건너뜁니다",
                })
                no_article_symbols.append(symbol)
                continue

            raw_articles = self._raw_article_repository.find_all(symbol=symbol)
            if not raw_articles:
                await _emit(on_event, {
                    "type": "progress",
                    "phase": "COLLECT",
                    "symbol": symbol,
                    "at": _now(),
                    "message": f"[{idx}/{total}] {name} — 수집된 기사 없음, 건너뜀",
                })
                no_article_symbols.append(symbol)
                continue

            news_articles = [r for r in raw_articles if r.source_type in NEWS_SOURCE_TYPES]
            report_articles = [r for r in raw_articles if r.source_type in REPORT_SOURCE_TYPES]
            selected_news = _select_articles(news_articles, article_mode)
            selected_reports = _select_articles(report_articles, article_mode)
            await _emit(on_event, {
                "type": "progress",
                "phase": "COLLECT",
                "symbol": symbol,
                "at": _now(),
                "message": (
                    f"[{idx}/{total}] {name} — "
                    f"뉴스 {len(news_articles)}건 중 {len(selected_news)}건, "
                    f"공시 {len(report_articles)}건 중 {len(selected_reports)}건 분석 예정"
                ),
            })
            symbol_data[symbol] = (item.name, selected_news, selected_reports)

        await _emit(on_event, {
            "type": "progress",
            "phase": "COLLECT",
            "at": _now(),
            "message": f"수집 완료. {len(symbol_data)}개 종목 AI 분석 시작...",
        })

        # Phase 2: AI 분석 (병렬 — DB 미사용)
        async def analyze_pair(symbol: str, name: str, news_arts, report_arts):
            await _emit(on_event, {
                "type": "progress",
                "phase": "ANALYZE",
                "symbol": symbol,
                "at": _now(),
                "message": f"{name}({symbol}) AI 분석 중...",
            })
            news_best, report_best = await asyncio.gather(
                self._analyze_articles(news_arts, symbol, name),
                self._analyze_articles(report_arts, symbol, name),
            )
            await _emit(on_event, {
                "type": "progress",
                "phase": "ANALYZE",
                "symbol": symbol,
                "at": _now(),
                "message": f"{name}({symbol}) 분석 완료",
            })
            return symbol, name, news_best, report_best

        analysis_results = await asyncio.gather(*[
            analyze_pair(symbol, name, news, report)
            for symbol, (name, news, report) in symbol_data.items()
        ])

        # Phase 3: 결과 집계
        results = [{"symbol": s, "skipped": True, "reason": "수집된 기사 없음"} for s in no_article_symbols]
        summaries = []
        report_summaries = []
        logs = []

        for symbol, name, news_best, report_best in analysis_results:
            if news_best:
                analysis, source_type, url, article_published_at, source_name = news_best
                tags = [t.label for t in analysis.tags]
                summaries.append(StockSummaryResponse(
                    symbol=symbol, name=name,
                    summary=analysis.summary, tags=tags,
                    sentiment=analysis.sentiment,
                    sentiment_score=analysis.sentiment_score,
                    confidence=analysis.confidence,
                    source_type=source_type,
                    url=url,
                    article_published_at=article_published_at,
                    source_name=source_name,
                ))
                logs.append(AnalysisLogResponse(
                    analyzed_at=datetime.now(), symbol=symbol, name=name,
                    summary=analysis.summary, tags=tags,
                    sentiment=analysis.sentiment,
                    sentiment_score=analysis.sentiment_score,
                    confidence=analysis.confidence,
                    source_type=source_type,
                    url=url,
                    article_published_at=article_published_at,
                    source_name=source_name,
                ))

            if report_best:
                analysis, source_type, url, article_published_at, source_name = report_best
                tags = [t.label for t in analysis.tags]
                report_summaries.append(StockSummaryResponse(
                    symbol=symbol, name=name,
                    summary=analysis.summary, tags=tags,
                    sentiment=analysis.sentiment,
                    sentiment_score=analysis.sentiment_score,
                    confidence=analysis.confidence,
                    source_type=source_type,
                    url=url,
                    article_published_at=article_published_at,
                    source_name=source_name,
                ))
                logs.append(AnalysisLogResponse(
                    analyzed_at=datetime.now(), symbol=symbol, name=name,
                    summary=analysis.summary, tags=tags,
                    sentiment=analysis.sentiment,
                    sentiment_score=analysis.sentiment_score,
                    confidence=analysis.confidence,
                    source_type=source_type,
                    url=url,
                    article_published_at=article_published_at,
                    source_name=source_name,
                ))

            if news_best or report_best:
                results.append({"symbol": symbol, "skipped": False})
            else:
                results.append({"symbol": symbol, "skipped": True, "reason": "분석 실패"})

        await _emit(on_event, {
            "type": "progress",
            "phase": "DONE",
            "at": _now(),
            "message": f"✅ 파이프라인 완료 — 뉴스 {len(summaries)}건, 공시·리포트 {len(report_summaries)}건",
        })

        return {
            "message": "파이프라인 완료",
            "processed": results,
            "summaries": summaries,
            "report_summaries": report_summaries,
            "logs": logs,
        }

    async def _analyze_articles(self, raw_articles, symbol: str, name: str):
        """기사 목록을 분석한다. 복수 기사는 종합 요약, 단건은 개별 분석."""
        if not raw_articles:
            return None

        if len(raw_articles) == 1 or self._analyzer_port is None:
            return await self._analyze_single_best(raw_articles, symbol)

        return await self._synthesize_multi(raw_articles, symbol, name)

    async def _analyze_single_best(self, raw_articles, symbol: str):
        """단건 분석: confidence 가장 높은 결과 반환 (캐시 활용)."""
        best_analysis = None
        best_source_type = None
        best_url = None
        best_published_at = None
        best_source_name = None

        for raw in raw_articles:
            try:
                published_at = _get_published_dt(raw)
                if published_at == datetime.min:
                    published_at = datetime.now()

                normalized = await self._normalize_usecase.execute(NormalizeRawArticleRequest(
                    id=str(raw.id),
                    source_type=raw.source_type,
                    source_name=raw.source_name,
                    title=raw.title,
                    body_text=raw.body_text or raw.title,
                    published_at=published_at,
                    symbol=raw.symbol,
                    lang=raw.lang or "ko",
                ))

                analysis = await self._analysis_usecase.execute(normalized.id)

                if best_analysis is None or analysis.confidence > best_analysis.confidence:
                    best_analysis = analysis
                    best_source_type = raw.source_type
                    best_url = getattr(raw, "url", None)
                    best_published_at = published_at if published_at != datetime.min else None
                    best_source_name = getattr(raw, "source_name", None)

            except Exception as e:
                logger.warning(f"[Pipeline] {symbol} 단건 분석 실패: {e}")
                continue

        if best_analysis is None:
            return None
        return best_analysis, best_source_type, best_url, best_published_at, best_source_name

    async def _synthesize_multi(self, raw_articles, symbol: str, name: str):
        """복수 기사 종합 요약: 최신순 정렬된 기사 전체를 1번의 AI 호출로 종합."""
        articles_data = []
        for raw in raw_articles:
            pub_dt = _get_published_dt(raw)
            pub_str = pub_dt.strftime("%Y-%m-%d %H:%M") if pub_dt != datetime.min else "날짜 미상"
            articles_data.append({
                "title": raw.title or "",
                "body": raw.body_text or raw.title or "",
                "published_at": pub_str,
            })

        try:
            analysis = await self._analyzer_port.synthesize_articles(
                symbol=symbol,
                name=name,
                articles=articles_data,
            )
        except Exception as e:
            logger.warning(f"[Pipeline] {symbol} 종합 분석 실패, 단건 폴백: {e}")
            return await self._analyze_single_best(raw_articles[:1], symbol)

        most_recent = raw_articles[0]
        pub_dt = _get_published_dt(most_recent)
        article_published_at = pub_dt if pub_dt != datetime.min else None
        return analysis, most_recent.source_type, getattr(most_recent, "url", None), article_published_at, getattr(most_recent, "source_name", None)
