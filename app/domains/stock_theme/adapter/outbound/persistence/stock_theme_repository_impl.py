from typing import Optional

from sqlalchemy.orm import Session

from app.domains.stock_theme.application.usecase.stock_theme_repository_port import StockThemeRepositoryPort
from app.domains.stock_theme.domain.entity.stock_theme import StockTheme
from app.domains.stock_theme.infrastructure.mapper.stock_theme_mapper import StockThemeMapper
from app.domains.stock_theme.infrastructure.orm.stock_theme_orm import StockThemeORM


class StockThemeRepositoryImpl(StockThemeRepositoryPort):
    def __init__(self, db: Session):
        self._db = db

    def save(self, item: StockTheme) -> StockTheme:
        existing = self._db.query(StockThemeORM).filter(StockThemeORM.code == item.code).first()
        if existing:
            existing.name = item.name
            existing.themes = item.themes
            self._db.commit()
            self._db.refresh(existing)
            return StockThemeMapper.to_entity(existing)
        orm = StockThemeMapper.to_orm(item)
        self._db.add(orm)
        self._db.commit()
        self._db.refresh(orm)
        return StockThemeMapper.to_entity(orm)

    def find_all(self) -> list[StockTheme]:
        orms = self._db.query(StockThemeORM).order_by(StockThemeORM.name).all()
        return [StockThemeMapper.to_entity(o) for o in orms]

    def find_by_code(self, code: str) -> Optional[StockTheme]:
        orm = self._db.query(StockThemeORM).filter(StockThemeORM.code == code).first()
        if orm is None:
            return None
        return StockThemeMapper.to_entity(orm)

    def find_by_theme(self, theme: str) -> list[StockTheme]:
        from sqlalchemy import func
        orms = self._db.query(StockThemeORM).filter(
            func.json_contains(StockThemeORM.themes, f'"{theme}"')
        ).all()
        return [StockThemeMapper.to_entity(o) for o in orms]
