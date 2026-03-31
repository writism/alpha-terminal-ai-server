from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class WatchlistStockData:
    symbol: str
    name: str
    market: str | None = None


@dataclass
class StockThemeData:
    code: str
    themes: list[str] = field(default_factory=list)


class MarketDataRepositoryPort(ABC):
    @abstractmethod
    def get_watchlist(self, account_id: int) -> list[WatchlistStockData]: ...

    @abstractmethod
    def get_stock_themes_by_codes(self, codes: list[str]) -> list[StockThemeData]: ...
