from sqlalchemy.orm import Session

from app.domains.market_analysis.application.usecase.stock_data_port import StockData, StockDataPort
from app.domains.stock_theme.infrastructure.orm.stock_theme_orm import StockThemeORM


class StockThemeDataAdapter(StockDataPort):
    """stock_themes 테이블에서 종목/테마 데이터를 조회한다."""

    def __init__(self, db: Session):
        self._db = db

    def find_all(self) -> list[StockData]:
        rows = self._db.query(StockThemeORM).all()
        return [
            StockData(name=row.name, code=row.code, themes=row.themes or [])
            for row in rows
        ]
