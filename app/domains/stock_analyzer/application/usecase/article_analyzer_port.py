from abc import ABC, abstractmethod

from app.domains.stock_analyzer.domain.entity.analyzed_article import AnalyzedArticle


class ArticleAnalyzerPort(ABC):
    @abstractmethod
    async def analyze(self, article_id: str, title: str, body: str, category: str) -> AnalyzedArticle:
        pass

    @abstractmethod
    async def synthesize_articles(self, symbol: str, name: str, articles: list[dict]) -> AnalyzedArticle:
        """여러 기사를 종합하여 하나의 분석 결과를 반환한다.

        articles: [{"title": ..., "body": ..., "published_at": ...}, ...]
        """
        pass
