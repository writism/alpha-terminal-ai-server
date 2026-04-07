from pydantic import BaseModel


class AnalyzeQuestionResponse(BaseModel):
    question: str
    answer: str
