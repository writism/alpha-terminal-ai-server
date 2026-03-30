from app.domains.stock_theme.application.usecase.stock_theme_repository_port import StockThemeRepositoryPort
from app.domains.stock_theme.domain.entity.stock_theme import StockTheme
from app.domains.stock_theme.domain.service.stock_theme_seed_data import SEED_DATA


class SeedStockThemesUseCase:
    def __init__(self, repository: StockThemeRepositoryPort):
        self._repository = repository

    def execute(self) -> int:
        count = 0
        for entry in SEED_DATA:
            item = StockTheme(
                name=entry["name"],
                code=entry["code"],
                themes=entry["themes"],
            )
            self._repository.save(item)
            count += 1
        return count
