from typing import List, Optional

from pydantic import BaseModel


class NewsArticleItem(BaseModel):
    title: str
    snippet: str
    source: str
    published_at: Optional[str] = None
    link: Optional[str] = None


class SearchNewsResponse(BaseModel):
    items: List[NewsArticleItem]
    total_count: int
    page: int
    page_size: int
