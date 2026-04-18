from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class StockSummaryResponse(BaseModel):
    symbol: str
    name: str
    summary: str
    tags: list
    sentiment: str
    sentiment_score: float
    confidence: float
    source_type: str = "NEWS"  # NEWS | DISCLOSURE | REPORT
    url: Optional[str] = None
    analyzed_at: Optional[datetime] = None
    article_published_at: Optional[datetime] = None
    source_name: Optional[str] = None
