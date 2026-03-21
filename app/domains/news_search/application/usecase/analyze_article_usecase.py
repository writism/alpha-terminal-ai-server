from app.domains.news_search.application.request.analyze_article_request import AnalyzeArticleRequest
from app.domains.news_search.application.response.analyze_article_response import AnalyzeArticleResponse
from app.domains.news_search.application.usecase.article_analysis_port import ArticleAnalysisPort
from app.domains.news_search.application.usecase.saved_article_repository_port import SavedArticleRepositoryPort


class AnalyzeArticleUseCase:
    def __init__(
        self,
        repository: SavedArticleRepositoryPort,
        analysis_port: ArticleAnalysisPort,
    ):
        self._repository = repository
        self._analysis_port = analysis_port

    async def execute(self, request: AnalyzeArticleRequest) -> AnalyzeArticleResponse:
        article = self._repository.find_by_id(request.article_id)
        if article is None:
            raise ValueError(f"기사를 찾을 수 없습니다: id={request.article_id}")

        if not article.content or not article.content.strip():
            raise ValueError("기사 본문이 비어 있어 분석할 수 없습니다.")

        result = await self._analysis_port.analyze(article.id, article.content)

        return AnalyzeArticleResponse(
            article_id=result.article_id,
            keywords=result.keywords,
            sentiment=result.sentiment,
            sentiment_score=result.sentiment_score,
        )
