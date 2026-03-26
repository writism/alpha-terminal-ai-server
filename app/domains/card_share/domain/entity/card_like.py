from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class CardLike:
    shared_card_id: int
    liker_ip: str
    id: Optional[int] = None
    liker_account_id: Optional[int] = None
    created_at: datetime = field(default_factory=datetime.now)
