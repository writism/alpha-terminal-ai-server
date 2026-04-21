from typing import Optional

from fastapi import APIRouter, Query
from fastapi.concurrency import run_in_threadpool

from app.domains.news_search.adapter.outbound.external.composite_news_search_adapter import CompositeNewsSearchAdapter
from app.domains.news_search.adapter.outbound.external.finnhub_news_search_adapter import FinnhubNewsSearchAdapter
from app.domains.news_search.adapter.outbound.external.naver_news_search_adapter import NaverNewsSearchAdapter
from app.domains.news_search.adapter.outbound.external.serp_news_search_adapter import SerpNewsSearchAdapter
from app.domains.news_search.application.response.search_news_response import SearchNewsResponse
from app.domains.news_search.application.usecase.search_news_usecase import SearchNewsUseCase

router = APIRouter(prefix="/news", tags=["news"])


def _build_adapter(market: Optional[str]):
    if market == "KR":
        serp = SerpNewsSearchAdapter(hl="ko", gl="kr")
        return CompositeNewsSearchAdapter([serp, NaverNewsSearchAdapter()])
    if market == "US":
        serp = SerpNewsSearchAdapter(hl="en", gl="us")
        return CompositeNewsSearchAdapter([serp, FinnhubNewsSearchAdapter()])
    return SerpNewsSearchAdapter()


@router.get("/search", response_model=SearchNewsResponse)
async def search_news(
    keyword: str = Query(..., min_length=1),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    market: Optional[str] = Query(default=None, description="US | KR"),
):
    adapter = _build_adapter(market)
    usecase = SearchNewsUseCase(adapter)
    return await run_in_threadpool(usecase.execute, keyword, page, page_size)
