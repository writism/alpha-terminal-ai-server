import logging

from app.domains.youtube.adapter.outbound.external.youtube_api_adapter import YouTubeApiAdapter
from app.domains.youtube.application.response.youtube_video_response import (
    YouTubeVideoListResponse,
    YouTubeVideoResponse,
)
from app.domains.youtube.application.usecase.youtube_video_repository_port import YouTubeVideoRepositoryPort

logger = logging.getLogger(__name__)


class CollectYouTubeVideosUseCase:
    def __init__(
        self,
        youtube_api: YouTubeApiAdapter,
        repository: YouTubeVideoRepositoryPort,
    ):
        self._youtube_api = youtube_api
        self._repository = repository

    async def execute(
        self,
        keywords: list[str],
        days: int = 3,
    ) -> YouTubeVideoListResponse:
        if not keywords:
            return YouTubeVideoListResponse(items=[], total_results=0)

        # 채널에서 키워드 기반 영상 수집
        videos = await self._youtube_api.collect_from_channels(
            keywords=keywords,
            days=days,
        )

        if not videos:
            return YouTubeVideoListResponse(items=[], total_results=0)

        # upsert: 중복이면 갱신, 신규면 저장
        saved = []
        for video in videos:
            try:
                existing = self._repository.find_by_video_id(video.video_id)
                if existing:
                    updated = self._repository.update(video)
                    saved.append(updated)
                else:
                    created = self._repository.save(video)
                    saved.append(created)
            except Exception as e:
                logger.warning(f"영상 저장 실패 (video_id={video.video_id}): {e}")
                continue

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
                for v in saved
            ],
            total_results=len(saved),
        )
