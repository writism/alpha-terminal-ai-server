from abc import ABC, abstractmethod
from typing import Optional

from app.domains.stock_theme.domain.entity.stock_theme import StockTheme


class StockThemeRepositoryPort(ABC):
    @abstractmethod
    def save(self, item: StockTheme) -> StockTheme:
        pass

    @abstractmethod
    def find_all(self) -> list[StockTheme]:
        pass

    @abstractmethod
    def find_by_code(self, code: str) -> Optional[StockTheme]:
        pass

    @abstractmethod
    def find_by_theme(self, theme: str) -> list[StockTheme]:
        pass
