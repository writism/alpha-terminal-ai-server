from typing import Optional

from app.domains.market_video.application.response.youtube_video_list_response import (
    YoutubeVideoItem,
    YoutubeVideoListResponse,
)
from app.domains.market_video.application.usecase.market_video_repository_port import MarketVideoRepositoryPort
from app.domains.market_video.application.usecase.youtube_search_port import YoutubeSearchPort

PAGE_SIZE = 9


class GetYoutubeVideoListUseCase:
    """market_videos DB에서 먼저 조회하고, 결과가 없으면 YouTube API로 fallback한다."""

    def __init__(
        self,
        repository: MarketVideoRepositoryPort,
        youtube_search: Optional[YoutubeSearchPort] = None,
    ):
        self._repository = repository
        self._youtube_search = youtube_search

    def execute(
        self,
        page_token: Optional[str],
        stock_name: Optional[str] = None,
    ) -> YoutubeVideoListResponse:
        page = int(page_token) if page_token and page_token.isdigit() else 1

        videos, total = self._repository.find_paginated(
            page=page,
            page_size=PAGE_SIZE,
            stock_name=stock_name,
        )

        # DB에 결과가 없고 YouTube API adapter가 있으면 실시간 검색 fallback
        if total == 0 and stock_name and self._youtube_search:
            try:
                api_videos, next_token, prev_token, api_total = self._youtube_search.search(
                    page_token=page_token if page_token and not page_token.isdigit() else None,
                    stock_name=stock_name,
                )
                return YoutubeVideoListResponse(
                    items=[
                        YoutubeVideoItem(
                            title=v.title,
                            thumbnail_url=v.thumbnail_url,
                            channel_name=v.channel_name,
                            published_at=v.published_at,
                            video_url=v.video_url,
                        )
                        for v in api_videos
                    ],
                    next_page_token=next_token,
                    prev_page_token=prev_token,
                    total_results=api_total,
                )
            except Exception:
                pass

        total_pages = (total + PAGE_SIZE - 1) // PAGE_SIZE
        next_token = str(page + 1) if page < total_pages else None
        prev_token = str(page - 1) if page > 1 else None

        return YoutubeVideoListResponse(
            items=[
                YoutubeVideoItem(
                    title=v.title,
                    thumbnail_url=v.thumbnail_url,
                    channel_name=v.channel_name,
                    published_at=v.published_at.isoformat(),
                    video_url=v.video_url,
                )
                for v in videos
            ],
            next_page_token=next_token,
            prev_page_token=prev_token,
            total_results=total,
        )
