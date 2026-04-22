from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, UniqueConstraint

from app.infrastructure.database.session import Base


class CardLikeORM(Base):
    __tablename__ = "card_likes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    shared_card_id = Column(Integer, ForeignKey("shared_cards.id", ondelete="CASCADE"), nullable=False)
    # 익명: 실제 IP, 로그인: "account:{account_id}" 형식으로 저장 (liker_identity 역할)
    liker_ip = Column(String(45), nullable=False)
    liker_account_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)

    __table_args__ = (
        UniqueConstraint("shared_card_id", "liker_ip", name="uq_card_like_ip"),
        UniqueConstraint("shared_card_id", "liker_account_id", name="uq_card_like_account"),
    )
