from pydantic import BaseModel, Field


class AnalysisQueryRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=500, description="분석 질문")
