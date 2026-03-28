from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text

from app.infrastructure.database.session import Base


class YouTubeVideoORM(Base):
    __tablename__ = "youtube_videos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    video_id = Column(String(20), unique=True, nullable=False, index=True)
    title = Column(Text, nullable=False)
    thumbnail_url = Column(Text, nullable=False)
    channel_name = Column(String(200), nullable=False)
    published_at = Column(String(50), nullable=False)
    video_url = Column(Text, nullable=False)
    view_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
