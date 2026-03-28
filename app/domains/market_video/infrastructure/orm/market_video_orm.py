from datetime import datetime

from sqlalchemy import BigInteger, Column, DateTime, Integer, String, Text

from app.infrastructure.database.session import Base


class MarketVideoORM(Base):
    __tablename__ = "market_videos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    video_id = Column(String(100), unique=True, nullable=False, index=True)
    title = Column(String(500), nullable=False)
    channel_name = Column(String(255), nullable=False)
    published_at = Column(DateTime, nullable=False)
    view_count = Column(BigInteger, default=0, nullable=False)
    thumbnail_url = Column(Text, nullable=False)
    video_url = Column(String(500), nullable=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)
