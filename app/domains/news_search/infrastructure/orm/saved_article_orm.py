from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text

from app.infrastructure.database.session import Base


class SavedArticleORM(Base):
    __tablename__ = "saved_articles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(500), nullable=False)
    link = Column(String(2048), nullable=False, unique=True)
    source = Column(String(255), nullable=False, default="")
    snippet = Column(Text, nullable=True)
    content = Column(Text, nullable=False)
    published_at = Column(String(100), nullable=True)
    saved_at = Column(DateTime, default=datetime.now)
