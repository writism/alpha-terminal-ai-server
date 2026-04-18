from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class InvestmentDecisionResponse(BaseModel):
    answer: str
    cached: bool = False
    cached_at: Optional[datetime] = None
