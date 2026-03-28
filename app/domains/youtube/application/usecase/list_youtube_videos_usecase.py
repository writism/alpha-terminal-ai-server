from app.domains.youtube.application.response.youtube_video_response import (
    YouTubeVideoListResponse,
    YouTubeVideoResponse,
)
from app.domains.youtube.application.usecase.youtube_search_port import YouTubeSearchPort


class ListYouTubeVideosUseCase:
    def __init__(self, youtube_search: YouTubeSearchPort):
        self._youtube_search = youtube_search

    async def execute(
        self, page_token: str | None = None,
    ) -> YouTubeVideoListResponse:
        videos, next_token, prev_token, total = await self._youtube_search.search_stock_videos(
            page_token=page_token,
        )
        return YouTubeVideoListResponse(
            items=[
                YouTubeVideoResponse(
                    video_id=v.video_id,
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
