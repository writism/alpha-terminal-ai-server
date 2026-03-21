from abc import ABC, abstractmethod

from app.domains.news_search.domain.entity.article_analysis import ArticleAnalysis


class ArticleAnalysisPort(ABC):
    @abstractmethod
    async def analyze(self, article_id: int, content: str) -> ArticleAnalysis:
        pass
