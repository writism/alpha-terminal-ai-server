from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text

from app.infrastructure.database.session import Base


class YouTubeCommentORM(Base):
    __tablename__ = "video_comments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    comment_id = Column(String(100), unique=True, nullable=False, index=True)
    video_id = Column(String(20), nullable=False, index=True)
    author_name = Column(String(200), nullable=False)
    text = Column(Text, nullable=False)
    published_at = Column(String(50), nullable=False)
    like_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
