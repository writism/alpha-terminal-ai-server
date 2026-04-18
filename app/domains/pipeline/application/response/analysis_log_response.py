from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class AnalysisLogResponse(BaseModel):
    analyzed_at: datetime
    symbol: str
    name: str
    summary: str
    tags: list[str]
    sentiment: str
    sentiment_score: float
    confidence: float
    source_type: str = "NEWS"
    account_id: Optional[int] = None
    url: Optional[str] = None
    article_published_at: Optional[datetime] = None
    source_name: Optional[str] = None
