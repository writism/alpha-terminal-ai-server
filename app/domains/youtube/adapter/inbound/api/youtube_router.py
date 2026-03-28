from typing import Optional

from fastapi import APIRouter, Cookie, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.domains.auth.adapter.outbound.in_memory.redis_session_adapter import RedisSessionAdapter
from app.domains.youtube.adapter.outbound.external.kiwi_noun_extractor import KiwiNounExtractor
from app.domains.youtube.adapter.outbound.external.youtube_api_adapter import YouTubeApiAdapter
from app.domains.youtube.adapter.outbound.persistence.youtube_comment_repository_impl import YouTubeCommentRepositoryImpl
from app.domains.youtube.adapter.outbound.persistence.youtube_video_repository_impl import YouTubeVideoRepositoryImpl
from app.domains.youtube.application.response.noun_frequency_response import NounFrequencyResponse
from app.domains.youtube.application.response.youtube_comment_response import YouTubeCommentListResponse
from app.domains.youtube.application.response.youtube_video_response import (
    YouTubeVideoListResponse,
    YouTubeVideoResponse,
)
from app.domains.youtube.application.usecase.collect_youtube_comments_usecase import CollectYouTubeCommentsUseCase
from app.domains.youtube.application.usecase.collect_youtube_videos_usecase import CollectYouTubeVideosUseCase
from app.domains.youtube.application.usecase.extract_nouns_usecase import ExtractNounsUseCase
from app.domains.youtube.application.usecase.list_youtube_videos_usecase import ListYouTubeVideosUseCase
from app.infrastructure.cache.redis_client import redis_client
from app.infrastructure.config.settings import get_settings
from app.infrastructure.database.session import get_db

router = APIRouter(prefix="/market-video", tags=["market-video"])

_session_adapter = RedisSessionAdapter(redis_client)


@router.get("/list", response_model=YouTubeVideoListResponse)
async def list_youtube_videos(
    page: int = 1,
    page_size: int = 9,
    page_token: str | None = None,
    db: Session = Depends(get_db),
):
    """DB에 저장된 영상 목록을 반환한다. DB가 비어있으면 YouTube API에서 직접 조회한다."""
    repo = YouTubeVideoRepositoryImpl(db)
    offset = (page - 1) * page_size
    videos, total = repo.find_all_ordered(limit=page_size, offset=offset)

    if total > 0:
        has_next = offset + page_size < total
        has_prev = page > 1
        return YouTubeVideoListResponse(
            items=[
                YouTubeVideoResponse(
                    video_id=v.video_id,
                    title=v.title,
                    thumbnail_url=v.thumbnail_url,
                    channel_name=v.channel_name,
                    published_at=v.published_at,
                    video_url=v.video_url,
                    view_count=v.view_count,
                )
                for v in videos
            ],
            next_page_token=str(page + 1) if has_next else None,
            prev_page_token=str(page - 1) if has_prev else None,
            total_results=total,
        )

    # DB가 비어있으면 기존 YouTube API 직접 조회 (fallback)
    settings = get_settings()
    adapter = YouTubeApiAdapter(api_key=settings.youtube_api_key)
    usecase = ListYouTubeVideosUseCase(youtube_search=adapter)
    return await usecase.execute(page_token=page_token)


@router.post("/collect", response_model=YouTubeVideoListResponse)
async def collect_youtube_videos(
    keywords: list[str] | None = None,
    days: int = 3,
    db: Session = Depends(get_db),
):
    """관심종목 키워드 기반으로 사전 정의된 채널에서 영상을 수집하여 DB에 저장한다."""
    if not keywords:
        return YouTubeVideoListResponse(items=[], total_results=0)

    settings = get_settings()
    adapter = YouTubeApiAdapter(api_key=settings.youtube_api_key)
    repo = YouTubeVideoRepositoryImpl(db)
    usecase = CollectYouTubeVideosUseCase(youtube_api=adapter, repository=repo)
    return await usecase.execute(keywords=keywords, days=days)


@router.get("/comments/{video_id}", response_model=YouTubeCommentListResponse)
async def get_video_comments(
    video_id: str,
    max_results: int = 100,
    order: str = "relevance",
    db: Session = Depends(get_db),
):
    """영상 ID로 댓글을 수집하고 DB에 저장한다. order: relevance(인기순) 또는 time(최신순)"""
    settings = get_settings()
    adapter = YouTubeApiAdapter(api_key=settings.youtube_api_key)
    comment_repo = YouTubeCommentRepositoryImpl(db)
    usecase = CollectYouTubeCommentsUseCase(youtube_comment=adapter, repository=comment_repo)
    return await usecase.execute(
        video_id=video_id,
        max_results=max_results,
        order=order,
    )


@router.get("/nouns/extract", response_model=NounFrequencyResponse)
def extract_nouns_from_comments(
    top_n: int = Query(default=30, ge=1, le=200),
    user_token: Optional[str] = Cookie(default=None),
    db: Session = Depends(get_db),
):
    """DB에 저장된 전체 댓글에서 명사를 추출하고 빈도수 기준으로 반환한다."""
    if not user_token:
        raise HTTPException(status_code=401, detail="인증이 필요합니다.")

    session = _session_adapter.find_by_token(user_token)
    if session is None:
        raise HTTPException(status_code=401, detail="세션이 만료되었거나 유효하지 않습니다.")

    comment_repo = YouTubeCommentRepositoryImpl(db)
    noun_extractor = KiwiNounExtractor()
    usecase = ExtractNounsUseCase(repository=comment_repo, noun_extractor=noun_extractor)
    return usecase.execute(top_n=top_n)
