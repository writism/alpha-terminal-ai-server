from pydantic import BaseModel


class RecommendationItem(BaseModel):
    name: str
    code: str
    matched_keywords: list[str]
    relevance_score: float
    recommendation_reason: str = ""


class RecommendationResponse(BaseModel):
    recommendations: list[RecommendationItem]
    total: int
    analyzed_keyword_count: int
