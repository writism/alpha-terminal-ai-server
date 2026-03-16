from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class SavedArticle:
    title: str
    link: str
    source: str
    content: str
    snippet: Optional[str] = None
    published_at: Optional[str] = None
    id: Optional[int] = None
    saved_at: datetime = field(default_factory=datetime.now)
