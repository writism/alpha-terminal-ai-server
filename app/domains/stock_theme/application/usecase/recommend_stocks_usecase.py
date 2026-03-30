from app.domains.stock_theme.application.response.recommendation_response import (
    RecommendationItem,
    RecommendationResponse,
)
from app.domains.stock_theme.application.usecase.stock_theme_repository_port import StockThemeRepositoryPort
from app.domains.stock_theme.domain.service.recommendation_reason_generation_service import (
    RecommendationReasonGenerationService,
)
from app.domains.stock_theme.domain.service.theme_match_service import ThemeMatchService


class RecommendStocksUseCase:
    def __init__(
        self,
        repository: StockThemeRepositoryPort,
        reason_service: RecommendationReasonGenerationService,
    ):
        self._repository = repository
        self._match_service = ThemeMatchService()
        self._reason_service = reason_service

    def execute(self, keyword_frequencies: dict[str, int]) -> RecommendationResponse:
        stock_themes = self._repository.find_all()
        theme_by_code = {s.code: list(s.themes) for s in stock_themes}
        results = self._match_service.match(keyword_frequencies, stock_themes)
        reasons = self._reason_service.build_reasons(results, theme_by_code)

        items = [
            RecommendationItem(
                name=r.name,
                code=r.code,
                matched_keywords=r.matched_keywords,
                relevance_score=r.relevance_score,
                recommendation_reason=reasons[i],
            )
            for i, r in enumerate(results)
        ]

        return RecommendationResponse(
            recommendations=items,
            total=len(items),
            analyzed_keyword_count=len(keyword_frequencies),
        )
