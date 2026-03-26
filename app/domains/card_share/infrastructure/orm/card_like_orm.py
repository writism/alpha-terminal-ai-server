from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, UniqueConstraint

from app.infrastructure.database.session import Base


class CardLikeORM(Base):
    __tablename__ = "card_likes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    shared_card_id = Column(Integer, nullable=False)
    liker_ip = Column(String(45), nullable=False)
    liker_account_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)

    __table_args__ = (
        UniqueConstraint("shared_card_id", "liker_ip", name="uq_card_like_ip"),
        UniqueConstraint("shared_card_id", "liker_account_id", name="uq_card_like_account"),
    )
