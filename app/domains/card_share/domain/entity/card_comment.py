from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class CardComment:
    shared_card_id: int
    content: str
    author_ip: str
    id: Optional[int] = None
    author_nickname: Optional[str] = None
    author_account_id: Optional[int] = None
    created_at: datetime = field(default_factory=datetime.now)
