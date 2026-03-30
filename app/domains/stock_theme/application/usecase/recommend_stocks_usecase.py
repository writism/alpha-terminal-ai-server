from app.domains.stock_theme.application.response.recommendation_response import (
    RecommendationItem,
    RecommendationResponse,
)
from app.domains.stock_theme.application.usecase.stock_theme_repository_port import StockThemeRepositoryPort
from app.domains.stock_theme.domain.service.theme_match_service import ThemeMatchService


class RecommendStocksUseCase:
    def __init__(self, repository: StockThemeRepositoryPort):
        self._repository = repository
        self._match_service = ThemeMatchService()

    def execute(self, keyword_frequencies: dict[str, int]) -> RecommendationResponse:
        stock_themes = self._repository.find_all()
        results = self._match_service.match(keyword_frequencies, stock_themes)

        items = [
            RecommendationItem(
                name=r.name,
                code=r.code,
                matched_keywords=r.matched_keywords,
                relevance_score=r.relevance_score,
            )
            for r in results
        ]

        return RecommendationResponse(
            recommendations=items,
            total=len(items),
            analyzed_keyword_count=len(keyword_frequencies),
        )
