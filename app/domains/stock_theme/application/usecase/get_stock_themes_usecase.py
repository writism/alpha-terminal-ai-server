from typing import Optional

from app.domains.stock_theme.application.response.stock_theme_response import (
    StockThemeListResponse,
    StockThemeResponse,
)
from app.domains.stock_theme.application.usecase.stock_theme_repository_port import StockThemeRepositoryPort


class GetStockThemesUseCase:
    def __init__(self, repository: StockThemeRepositoryPort):
        self._repository = repository

    def execute(self, theme: Optional[str] = None) -> StockThemeListResponse:
        if theme:
            items = self._repository.find_by_theme(theme)
        else:
            items = self._repository.find_all()

        responses = [
            StockThemeResponse(
                id=item.id,
                name=item.name,
                code=item.code,
                themes=item.themes,
            )
            for item in items
        ]
        return StockThemeListResponse(items=responses, total=len(responses))
