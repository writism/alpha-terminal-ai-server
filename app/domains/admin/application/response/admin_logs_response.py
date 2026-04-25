from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class AdminLogItem(BaseModel):
    id: int
    symbol: str
    name: str
    analyzed_at: datetime
    sentiment: str
    sentiment_score: float
    source_type: Optional[str]
    account_id: Optional[int]


class AdminLogsResponse(BaseModel):
    logs: List[AdminLogItem]
    total: int
