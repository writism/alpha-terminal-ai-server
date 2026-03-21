from pydantic import BaseModel


class StockSummaryResponse(BaseModel):
    symbol: str
    name: str
    summary: str
    tags: list
    sentiment: str
    sentiment_score: float
    confidence: float
