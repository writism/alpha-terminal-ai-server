from datetime import datetime, timedelta
from hashlib import sha256
from typing import List

import httpx

from app.domains.stock_collector.application.usecase.collector_port import CollectorPort
from app.domains.stock_collector.domain.entity.raw_article import RawArticle
from app.infrastructure.config.settings import get_settings


class DartCollectorAdapter(CollectorPort):
    DART_API_URL = "https://opendart.fss.or.kr/api/list.json"

    def collect(self, symbol: str) -> List[RawArticle]:
        settings = get_settings()

        params = {
            "crtfc_key": settings.dart_api_key,
            "corp_code": self._get_corp_code(symbol),
            "bgn_de": (datetime.now() - timedelta(days=30)).strftime("%Y%m%d"),
            "end_de": datetime.now().strftime("%Y%m%d"),
            "page_no": "1",
            "page_count": "10",
        }

        try:
            response = httpx.get(self.DART_API_URL, params=params, timeout=10.0)
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPError:
            return []

        if data.get("status") != "000":
            return []

        articles = []
        now = datetime.now().isoformat()

        for item in data.get("list", []):
            rcp_no = item.get("rcept_no", "")
            body_text = f"{item.get('report_nm', '')} - {item.get('flr_nm', '')}"
            content = body_text.encode()

            articles.append(
                RawArticle(
                    source_type="DISCLOSURE",
                    source_name="DART",
                    source_doc_id=rcp_no,
                    url=f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={rcp_no}",
                    title=item.get("report_nm", ""),
                    body_text=body_text,
                    published_at=item.get("rcept_dt", ""),
                    collected_at=now,
                    symbol=symbol,
                    market=item.get("corp_cls", ""),
                    content_hash=f"sha256:{sha256(content).hexdigest()}",
                    collector_version="collector-v1.0.0",
                    status="COLLECTED",
                    author="금융감독원 전자공시시스템",
                    meta={
                        "report_type": item.get("report_nm", ""),
                        "corp_name": item.get("corp_name", ""),
                        "rcp_no": rcp_no,
                    },
                )
            )

        return articles

    # 종목코드 → DART 고유번호 매핑
    SYMBOL_TO_CORP_CODE = {
        "005930": "00126380",  # 삼성전자
        "000660": "00164779",  # SK하이닉스
        "035420": "00401731",  # 네이버
        "035720": "00918444",  # 카카오
        "373220": "01596594",  # LG에너지솔루션
        "005380": "00164742",  # 현대차
        "000270": "00113971",  # 기아
        "051910": "00131485",  # LG화학
        "006400": "00131372",  # 삼성SDI
        "068270": "00259103",  # 셀트리온
        "207940": "00434003",  # 삼성바이오로직스
        "005490": "00104426",  # POSCO홀딩스
        "000810": "00126955",  # 삼성화재
        "012330": "00164788",  # 현대모비스
        "028260": "00104256",  # 삼성물산
        "066570": "00119548",  # LG전자
        "003550": "00115012",  # LG
        "015760": "00159643",  # 한국전력
        "096770": "00241701",  # SK이노베이션
        "017670": "00144117",  # SK텔레콤
        "030200": "00113028",  # KT
        "032830": "00115388",  # 삼성생명
        "009150": "00126380",  # 삼성전기
        "010130": "00115012",  # 고려아연
        "011200": "00112216",  # HMM
    }

    def _get_corp_code(self, symbol: str) -> str:
        return self.SYMBOL_TO_CORP_CODE.get(symbol, symbol)
