from abc import ABC, abstractmethod
from typing import Optional

from app.domains.youtube.domain.entity.youtube_video import YouTubeVideo


class YouTubeVideoRepositoryPort(ABC):
    @abstractmethod
    def find_by_video_id(self, video_id: str) -> Optional[YouTubeVideo]:
        ...

    @abstractmethod
    def save(self, video: YouTubeVideo) -> YouTubeVideo:
        ...

    @abstractmethod
    def update(self, video: YouTubeVideo) -> YouTubeVideo:
        ...

    @abstractmethod
    def find_all_ordered(self, limit: int = 9, offset: int = 0) -> tuple[list[YouTubeVideo], int]:
        """Returns (videos, total_count) ordered by published_at desc."""
        ...
