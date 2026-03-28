from typing import Optional

from fastapi import APIRouter, Cookie, Depends, HTTPException
from sqlalchemy.orm import Session

from app.domains.auth.adapter.outbound.in_memory.redis_session_adapter import RedisSessionAdapter
from app.domains.market_video.adapter.outbound.external.youtube_channel_video_adapter import (
    YoutubeChannelVideoAdapter,
)
from app.domains.market_video.adapter.outbound.persistence.market_video_repository_impl import (
    MarketVideoRepositoryImpl,
)
from app.domains.market_video.application.response.collect_market_video_response import CollectMarketVideoResponse
from app.domains.market_video.application.usecase.collect_market_video_usecase import CollectMarketVideoUseCase
from app.domains.watchlist.adapter.outbound.persistence.watchlist_repository_impl import WatchlistRepositoryImpl
from app.infrastructure.cache.redis_client import redis_client
from app.infrastructure.database.session import get_db

router = APIRouter(prefix="/youtube", tags=["youtube"])

_session_adapter = RedisSessionAdapter(redis_client)


@router.post("/collect", response_model=CollectMarketVideoResponse)
async def collect_market_videos(
    user_token: Optional[str] = Cookie(default=None),
    db: Session = Depends(get_db),
):
    """사용자 관심종목 기반으로 채널에서 영상을 수집하여 DB에 저장한다."""
    if not user_token:
        raise HTTPException(status_code=401, detail="인증이 필요합니다.")
    session = _session_adapter.find_by_token(user_token)
    if session is None:
        raise HTTPException(status_code=401, detail="유효하지 않거나 만료된 세션입니다.")

    account_id = int(session.user_id)
    watchlist_items = WatchlistRepositoryImpl(db).find_all(account_id=account_id)
    stock_names = [item.name for item in watchlist_items]

    usecase = CollectMarketVideoUseCase(
        channel_video_port=YoutubeChannelVideoAdapter(),
        repository=MarketVideoRepositoryImpl(db),
    )
    return usecase.execute(stock_names)
