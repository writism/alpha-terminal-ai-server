from sqlalchemy import Column, Integer, String
from sqlalchemy.dialects.mysql import JSON

from app.infrastructure.database.session import Base


class StockThemeORM(Base):
    __tablename__ = "stock_themes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    code = Column(String(20), nullable=False, unique=True)
    themes = Column(JSON, nullable=False, default=list)
