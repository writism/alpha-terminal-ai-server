from pydantic import BaseModel


class AnalysisAnswerResponse(BaseModel):
    question: str
    answer: str
    in_scope: bool
    is_personalized: bool = False
