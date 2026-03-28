from abc import ABC, abstractmethod

from app.domains.youtube.domain.entity.youtube_comment import YouTubeComment


class YouTubeCommentRepositoryPort(ABC):
    @abstractmethod
    def upsert(self, comment: YouTubeComment) -> YouTubeComment:
        ...

    @abstractmethod
    def find_by_video_id(self, video_id: str) -> list[YouTubeComment]:
        ...

    @abstractmethod
    def find_all(self) -> list[YouTubeComment]:
        ...
