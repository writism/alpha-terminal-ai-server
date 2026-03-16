from datetime import datetime
from hashlib import sha256

from sqlalchemy import Column, DateTime, Integer, String, Text, event

from app.infrastructure.database.session import Base


class SavedArticleORM(Base):
    __tablename__ = "saved_articles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(500), nullable=False)
    link = Column(Text, nullable=False)
    link_hash = Column(String(64), nullable=False, unique=True)
    source = Column(String(255), nullable=False, default="")
    snippet = Column(Text, nullable=True)
    content = Column(Text, nullable=False)
    published_at = Column(String(100), nullable=True)
    saved_at = Column(DateTime, default=datetime.now)


@event.listens_for(SavedArticleORM, "before_insert")
def generate_link_hash(mapper, connection, target):
    if target.link:
        target.link_hash = sha256(target.link.encode()).hexdigest()
