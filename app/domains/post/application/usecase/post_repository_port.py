from abc import ABC, abstractmethod

from app.domains.post.domain.entity.post import Post


class PostRepositoryPort(ABC):
    @abstractmethod
    def save(self, post: Post) -> Post:
        pass
