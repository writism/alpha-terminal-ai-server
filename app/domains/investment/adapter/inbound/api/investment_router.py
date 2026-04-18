import asyncio
import json
from typing import Optional

from fastapi import APIRouter, Cookie, Depends, Header, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.domains.auth.adapter.outbound.in_memory.redis_session_adapter import RedisSessionAdapter
from app.domains.investment.adapter.outbound.agent import log_context
from app.domains.investment.adapter.outbound.external.langgraph_investment_adapter import LangGraphInvestmentAdapter
from app.domains.investment.adapter.outbound.external.youtube_sentiment_adapter import YouTubeSentimentAdapter
from app.domains.investment.application.request.investment_decision_request import InvestmentDecisionRequest
from app.domains.investment.application.request.youtube_sentiment_request import YouTubeSentimentRequest
from app.domains.investment.application.response.investment_decision_response import InvestmentDecisionResponse
from app.domains.investment.application.response.youtube_sentiment_response import (
    SentimentDistribution,
    YouTubeSentimentResponse,
)
from app.domains.investment.application.usecase.investment_decision_usecase import InvestmentDecisionUseCase
from app.domains.investment.application.usecase.youtube_sentiment_usecase import YouTubeSentimentUseCase
from app.domains.investment.infrastructure.repository.analysis_cache_repository import AnalysisCacheRepository
from app.infrastructure.cache.redis_client import redis_client
from app.infrastructure.database.pg_session import get_pg_db, PgSessionLocal

router = APIRouter(prefix="/investment", tags=["investment"])

_session_adapter = RedisSessionAdapter(redis_client)


def _resolve_account_id(
    account_id_cookie: Optional[str],
    user_token: Optional[str],
    x_account_id: Optional[str] = None,
) -> Optional[int]:
    # Swagger UI 테스트용 헤더 (X-Account-Id) 우선 확인
    if x_account_id:
        try:
            return int(x_account_id)
        except ValueError:
            pass
    if account_id_cookie:
        try:
            return int(account_id_cookie)
        except ValueError:
            pass
    if user_token:
        session = _session_adapter.find_by_token(user_token)
        if session:
            try:
                return int(session.user_id)
            except ValueError:
                pass
    return None


@router.post("/decision", response_model=InvestmentDecisionResponse)
async def investment_decision(
    request: InvestmentDecisionRequest,
    account_id: Optional[str] = Cookie(default=None),
    user_token: Optional[str] = Cookie(default=None),
    x_account_id: Optional[str] = Header(default=None),
    db: Session = Depends(get_pg_db),
):
    """인증된 사용자의 투자 판단 질의를 LangGraph 멀티 에이전트로 처리한다.

    force=False(기본)이면 1시간 이내 캐시된 결과를 즉시 반환한다.
    force=True이면 캐시를 무시하고 파이프라인을 재실행한다.
    """
    aid = _resolve_account_id(account_id, user_token, x_account_id)
    if aid is None:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")

    if not request.symbol:
        raise HTTPException(status_code=422, detail="symbol 필드가 필요합니다.")

    cache_repo = AnalysisCacheRepository(db)

    if not request.force:
        cached = cache_repo.find_valid(request.symbol)
        if cached:
            return InvestmentDecisionResponse(
                answer=cached.answer,
                cached=True,
                cached_at=cached.created_at,
            )

    adapter = LangGraphInvestmentAdapter()
    usecase = InvestmentDecisionUseCase(adapter)
    decision = await usecase.execute(query=request.query)

    cache_repo.save(
        symbol=request.symbol,
        query=request.query,
        answer=decision.answer,
    )

    return InvestmentDecisionResponse(answer=decision.answer)


def _lookup_symbol_by_name(company_name: str) -> Optional[str]:
    """company명으로 종목 symbol을 동기 조회한다."""
    from app.domains.stock.infrastructure.orm.stock_orm import StockORM
    from app.infrastructure.database.session import SessionLocal

    db = SessionLocal()
    try:
        orm = db.query(StockORM).filter(StockORM.name == company_name).first()
        if not orm:
            orm = db.query(StockORM).filter(StockORM.name.like(f"%{company_name}%")).first()
        return orm.symbol if orm else None
    finally:
        db.close()


def _find_cached_answer(symbol: str, force: bool) -> Optional[str]:
    """symbol 기준 유효 캐시를 동기 조회한다. force=True 이면 None 반환."""
    if force:
        return None
    db = PgSessionLocal()
    try:
        cached = AnalysisCacheRepository(db).find_valid(symbol)
        return cached.answer if cached else None
    finally:
        db.close()


def _save_cache(symbol: str, query: str, answer: str) -> None:
    """분석 결과를 캐시에 동기 저장한다."""
    db = PgSessionLocal()
    try:
        AnalysisCacheRepository(db).save(symbol=symbol, query=query, answer=answer)
    finally:
        db.close()


@router.post("/decision/stream")
async def investment_decision_stream(
    request: InvestmentDecisionRequest,
    account_id: Optional[str] = Cookie(default=None),
    user_token: Optional[str] = Cookie(default=None),
    x_account_id: Optional[str] = Header(default=None),
):
    """인증된 사용자의 투자 판단 질의를 SSE 스트림으로 처리한다.

    캐시 흐름:
        1. request.symbol 또는 QueryParser 추출 company명 → symbol 조회
        2. 유효 캐시(1시간) 존재 시 → 캐시된 결과를 즉시 스트림 반환
        3. 캐시 없음 → 전체 워크플로우 실행 → 결과 캐시 저장

    이벤트 유형:
        {"type": "log",    "data": "로그 메시지"}
        {"type": "result", "data": "최종 응답"}
        {"type": "error",  "data": "오류 메시지"}
        {"type": "end"}
    """
    aid = _resolve_account_id(account_id, user_token, x_account_id)
    if aid is None:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")

    # symbol 확정: 요청에 포함된 경우 그대로 사용, 없으면 QueryParser로 추출 후 DB 조회
    resolved_symbol: Optional[str] = request.symbol

    if not resolved_symbol:
        try:
            from app.domains.investment.adapter.outbound.agent.query_parser import parse_investment_query
            from app.domains.investment.adapter.outbound.agent.log_context import set_log_queue, reset_log_queue

            _pre_q: asyncio.Queue = asyncio.Queue(maxsize=100)
            _pre_token = set_log_queue(_pre_q)
            try:
                parsed = await parse_investment_query(request.query)
            finally:
                reset_log_queue(_pre_token)

            company = parsed.get("company")
            if company:
                loop = asyncio.get_event_loop()
                resolved_symbol = await loop.run_in_executor(None, _lookup_symbol_by_name, company)
        except Exception:
            resolved_symbol = None

    # 캐시 히트 시 즉시 반환
    if resolved_symbol and not request.force:
        loop = asyncio.get_event_loop()
        cached_answer = await loop.run_in_executor(
            None, _find_cached_answer, resolved_symbol, request.force
        )
        if cached_answer:
            async def _cached_generator():
                yield f"data: {json.dumps({'type': 'log', 'data': f'[Cache] ✓ 캐시된 분석 결과 반환 ({resolved_symbol})'}, ensure_ascii=False)}\n\n"
                yield f"data: {json.dumps({'type': 'result', 'data': cached_answer}, ensure_ascii=False)}\n\n"
                yield f"data: {json.dumps({'type': 'end'}, ensure_ascii=False)}\n\n"

            return StreamingResponse(
                _cached_generator(),
                media_type="text/event-stream",
                headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
            )

    q: asyncio.Queue = asyncio.Queue(maxsize=2000)

    # 현재 컨텍스트에 큐 등록 → create_task 시 복사됨
    token = log_context.set_log_queue(q)

    _symbol_for_cache = resolved_symbol

    async def _run_workflow():
        try:
            adapter = LangGraphInvestmentAdapter()
            usecase = InvestmentDecisionUseCase(adapter)
            decision = await usecase.execute(query=request.query)
            await q.put({"type": "result", "data": decision.answer})

            # 워크플로우 완료 후 캐시 저장
            if _symbol_for_cache:
                try:
                    loop = asyncio.get_event_loop()
                    await loop.run_in_executor(
                        None, _save_cache, _symbol_for_cache, request.query, decision.answer
                    )
                except Exception:
                    pass
        except Exception as e:
            await q.put({"type": "error", "data": str(e)})
        finally:
            await q.put({"type": "end"})

    # 백그라운드 태스크 — 현재 컨텍스트(큐 포함)를 복사하여 실행
    asyncio.create_task(_run_workflow())

    # 이 핸들러 컨텍스트에서는 큐 해제 (태스크는 복사본 보유)
    log_context.reset_log_queue(token)

    async def event_generator():
        while True:
            try:
                msg = await asyncio.wait_for(q.get(), timeout=120.0)
            except asyncio.TimeoutError:
                yield f"data: {json.dumps({'type': 'error', 'data': '응답 타임아웃 (120s)'}, ensure_ascii=False)}\n\n"
                break

            yield f"data: {json.dumps(msg, ensure_ascii=False)}\n\n"

            if msg["type"] in ("end", "error"):
                break

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/youtube-sentiment", response_model=YouTubeSentimentResponse)
async def youtube_sentiment_analysis(
    request: YouTubeSentimentRequest,
    account_id: Optional[str] = Cookie(default=None),
    user_token: Optional[str] = Cookie(default=None),
    x_account_id: Optional[str] = Header(default=None),
):
    """저장된 YouTube 댓글로 투자 심리 지표를 산출한다.

    - company: 종목명으로 최근 수집 댓글 조회 (예: "삼성전자")
    - log_id : investment_youtube_logs.id로 특정 수집 세션 댓글 조회

    둘 중 하나는 반드시 지정해야 한다. log_id 가 지정되면 company 보다 우선한다.

    **Swagger 테스트**: x-account-id 헤더에 임의 숫자(예: 1) 입력
    """
    aid = _resolve_account_id(account_id, user_token, x_account_id)
    if aid is None:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")

    try:
        adapter = YouTubeSentimentAdapter()
        usecase = YouTubeSentimentUseCase(adapter)
        metrics = await usecase.execute(company=request.company, log_id=request.log_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    sd = metrics.get("sentiment_distribution", {})
    return YouTubeSentimentResponse(
        sentiment_distribution=SentimentDistribution(
            positive=sd.get("positive", 0.0),
            neutral=sd.get("neutral", 1.0),
            negative=sd.get("negative", 0.0),
        ),
        sentiment_score=metrics.get("sentiment_score", 0.0),
        bullish_keywords=metrics.get("bullish_keywords", []),
        bearish_keywords=metrics.get("bearish_keywords", []),
        topics=metrics.get("topics", []),
        volume=metrics.get("volume", 0),
    )
