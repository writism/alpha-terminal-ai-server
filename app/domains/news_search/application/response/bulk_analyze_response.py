from typing import List

from pydantic import BaseModel


class BulkAnalyzeItem(BaseModel):
    article_id: int
    title: str
    sentiment: str
    sentiment_score: float
    keywords: List[str]


class BulkAnalyzeResponse(BaseModel):
    query: str
    total: int
    results: List[BulkAnalyzeItem]
