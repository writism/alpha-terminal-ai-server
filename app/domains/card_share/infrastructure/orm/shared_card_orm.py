from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, JSON, String, Text

from app.infrastructure.database.session import Base


class SharedCardORM(Base):
    __tablename__ = "shared_cards"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), nullable=False)
    name = Column(String(100), nullable=False)
    summary = Column(Text, nullable=False)
    tags = Column(JSON, nullable=False, default=list)
    sentiment = Column(String(20), nullable=False)
    sentiment_score = Column(Float, nullable=False)
    confidence = Column(Float, nullable=False)
    source_type = Column(String(20), nullable=False, default="NEWS")
    url = Column(String(500), nullable=True)
    analyzed_at = Column(DateTime, nullable=False)
    sharer_account_id = Column(Integer, nullable=True)
    sharer_nickname = Column(String(100), nullable=True)
    like_count = Column(Integer, nullable=False, default=0)
    comment_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
