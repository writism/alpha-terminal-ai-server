from abc import ABC, abstractmethod

from app.domains.youtube.domain.entity.youtube_video import YouTubeVideo


class YouTubeSearchPort(ABC):
    @abstractmethod
    async def search_stock_videos(
        self, page_token: str | None = None, max_results: int = 9,
    ) -> tuple[list[YouTubeVideo], str | None, str | None, int]:
        """Returns (videos, next_page_token, prev_page_token, total_results)."""
        ...
