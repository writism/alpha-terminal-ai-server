from pydantic import BaseModel


class AnalysisAnswerResponse(BaseModel):
    answer: str
    in_scope: bool
