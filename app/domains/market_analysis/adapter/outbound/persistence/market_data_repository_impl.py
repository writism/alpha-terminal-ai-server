from sqlalchemy.orm import Session

from app.domains.market_analysis.application.usecase.market_data_repository_port import (
    MarketDataRepositoryPort,
    StockThemeData,
    WatchlistStockData,
)
from app.domains.stock_theme.infrastructure.orm.stock_theme_orm import StockThemeORM
from app.domains.watchlist.infrastructure.orm.watchlist_item_orm import WatchlistItemORM


class MarketDataRepositoryImpl(MarketDataRepositoryPort):
    def __init__(self, db: Session):
        self._db = db

    def get_watchlist(self, account_id: int) -> list[WatchlistStockData]:
        orms = (
            self._db.query(WatchlistItemORM)
            .filter(WatchlistItemORM.account_id == account_id)
            .all()
        )
        return [WatchlistStockData(symbol=o.symbol, name=o.name, market=o.market) for o in orms]

    def get_stock_themes_by_codes(self, codes: list[str]) -> list[StockThemeData]:
        if not codes:
            return []
        import json
        orms = (
            self._db.query(StockThemeORM)
            .filter(StockThemeORM.code.in_(codes))
            .all()
        )
        result = []
        for o in orms:
            themes = o.themes if isinstance(o.themes, list) else json.loads(o.themes or "[]")
            result.append(StockThemeData(code=o.code, themes=themes))
        return result
