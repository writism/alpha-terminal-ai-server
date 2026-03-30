from app.domains.stock_theme.domain.entity.stock_theme import StockTheme
from app.domains.stock_theme.infrastructure.orm.stock_theme_orm import StockThemeORM


class StockThemeMapper:
    @staticmethod
    def to_entity(orm: StockThemeORM) -> StockTheme:
        return StockTheme(
            id=orm.id,
            name=orm.name,
            code=orm.code,
            themes=orm.themes or [],
        )

    @staticmethod
    def to_orm(entity: StockTheme) -> StockThemeORM:
        return StockThemeORM(
            name=entity.name,
            code=entity.code,
            themes=entity.themes,
        )
