from typing import Optional

from pydantic import BaseModel, Field


class InvestmentDecisionRequest(BaseModel):
    query: str = Field(..., min_length=1, description="투자 판단 질의 텍스트")
    symbol: Optional[str] = Field(default=None, description="종목 코드 (캐시 키, 없으면 company명으로 자동 조회)")
    force: bool = Field(default=False, description="캐시 무시하고 강제 재분석")
