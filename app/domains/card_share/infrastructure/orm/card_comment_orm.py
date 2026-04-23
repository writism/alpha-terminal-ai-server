from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text

from app.infrastructure.database.session import Base


class CardCommentORM(Base):
    __tablename__ = "card_comments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    shared_card_id = Column(Integer, nullable=False)
    content = Column(String(120), nullable=False)
    author_nickname = Column(String(100), nullable=True)
    author_account_id = Column(Integer, nullable=True)
    author_ip = Column(String(45), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
