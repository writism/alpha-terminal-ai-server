from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class SaveArticleResponse(BaseModel):
    id: int
    title: str
    link: str
    source: str
    snippet: Optional[str] = None
    content: str
    published_at: Optional[str] = None
    saved_at: datetime
