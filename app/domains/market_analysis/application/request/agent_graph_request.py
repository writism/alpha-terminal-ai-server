from pydantic import BaseModel, Field


class AgentGraphRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500, description="분석 질문")
