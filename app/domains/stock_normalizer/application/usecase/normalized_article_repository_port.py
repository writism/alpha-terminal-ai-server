from abc import ABC, abstractmethod

from app.domains.stock_normalizer.domain.entity.normalized_article import NormalizedArticle


class NormalizedArticleRepositoryPort(ABC):
    @abstractmethod
    async def save(self, article: NormalizedArticle) -> NormalizedArticle:
        pass
