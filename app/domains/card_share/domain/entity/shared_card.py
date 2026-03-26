from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class SharedCard:
    symbol: str
    name: str
    summary: str
    tags: list
    sentiment: str
    sentiment_score: float
    confidence: float
    source_type: str
    analyzed_at: datetime
    id: Optional[int] = None
    url: Optional[str] = None
    sharer_account_id: Optional[int] = None
    sharer_nickname: Optional[str] = None
    like_count: int = 0
    comment_count: int = 0
    created_at: datetime = field(default_factory=datetime.now)
