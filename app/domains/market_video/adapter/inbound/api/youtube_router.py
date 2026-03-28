from typing import Optional

from fastapi import APIRouter, Cookie, HTTPException, Query

from app.domains.auth.adapter.outbound.in_memory.redis_session_adapter import RedisSessionAdapter
from app.domains.market_video.adapter.outbound.external.youtube_search_adapter import YoutubeSearchAdapter
from app.domains.market_video.application.response.youtube_video_list_response import YoutubeVideoListResponse
from app.domains.market_video.application.usecase.get_youtube_video_list_usecase import GetYoutubeVideoListUseCase
from app.infrastructure.cache.redis_client import redis_client

router = APIRouter(prefix="/youtube", tags=["youtube"])

_session_adapter = RedisSessionAdapter(redis_client)


@router.get("/list", response_model=YoutubeVideoListResponse)
async def get_youtube_video_list(
    stock_name: Optional[str] = Query(default=None, description="검색할 관심종목 이름"),
    page_token: Optional[str] = Query(default=None, description="YouTube 페이지 토큰"),
    user_token: Optional[str] = Cookie(default=None),
):
    if not user_token:
        raise HTTPException(status_code=401, detail="인증이 필요합니다.")
    session = _session_adapter.find_by_token(user_token)
    if session is None:
        raise HTTPException(status_code=401, detail="유효하지 않거나 만료된 세션입니다.")

    usecase = GetYoutubeVideoListUseCase(YoutubeSearchAdapter())
    return usecase.execute(page_token, stock_name)
