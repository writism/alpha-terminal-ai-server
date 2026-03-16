from typing import Optional

from pydantic import BaseModel, Field


class SaveArticleRequest(BaseModel):
    title: str = Field(..., min_length=1)
    link: str = Field(..., min_length=1)
    source: str = Field(default="")
    snippet: Optional[str] = None
    published_at: Optional[str] = None
