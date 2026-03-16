from dataclasses import dataclass
from typing import Optional


@dataclass
class NewsArticle:
    title: str
    snippet: str
    source: str
    published_at: Optional[str] = None
    link: Optional[str] = None
