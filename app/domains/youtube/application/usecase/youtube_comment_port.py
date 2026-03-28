from abc import ABC, abstractmethod

from app.domains.youtube.domain.entity.youtube_comment import YouTubeComment


class YouTubeCommentPort(ABC):
    @abstractmethod
    async def fetch_comments(
        self,
        video_id: str,
        max_results: int = 100,
        order: str = "relevance",
    ) -> list[YouTubeComment]:
        """영상 ID로 댓글을 조회한다."""
        ...
