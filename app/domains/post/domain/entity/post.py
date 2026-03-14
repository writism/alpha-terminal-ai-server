from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Post:
    title: str
    content: str
    author: str = "익명"
    id: Optional[int] = None
    created_at: datetime = field(default_factory=datetime.now)
