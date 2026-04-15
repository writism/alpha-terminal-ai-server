from typing import Optional

from pydantic import BaseModel


class AgentGraphResponse(BaseModel):
    query: str
    plan: Optional[str]
    analysis: Optional[str]
    final_output: Optional[str]
    review_passed: Optional[bool]
