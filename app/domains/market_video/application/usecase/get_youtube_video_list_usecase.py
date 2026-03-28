from typing import Optional

from app.domains.market_video.application.response.youtube_video_list_response import (
    YoutubeVideoItem,
    YoutubeVideoListResponse,
)
from app.domains.market_video.application.usecase.youtube_search_port import YoutubeSearchPort


class GetYoutubeVideoListUseCase:
    def __init__(self, youtube_search_port: YoutubeSearchPort):
        self._port = youtube_search_port

    def execute(self, page_token: Optional[str], stock_name: Optional[str] = None) -> YoutubeVideoListResponse:
        videos, next_token, prev_token, total = self._port.search(page_token, stock_name)
        return YoutubeVideoListResponse(
            items=[
                YoutubeVideoItem(
                    title=v.title,
                    thumbnail_url=v.thumbnail_url,
                    channel_name=v.channel_name,
                    published_at=v.published_at,
                    video_url=v.video_url,
                )
                for v in videos
            ],
            next_page_token=next_token,
            prev_page_token=prev_token,
            total_results=total,
        )
