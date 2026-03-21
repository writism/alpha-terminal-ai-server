from typing import List

from pydantic import BaseModel


class AnalyzeArticleResponse(BaseModel):
    article_id: int
    keywords: List[str]
    sentiment: str          # POSITIVE | NEGATIVE | NEUTRAL
    sentiment_score: float  # -1.0 ~ 1.0
