from pydantic import BaseModel


class NounFrequencyItem(BaseModel):
    noun: str
    count: int


class NounFrequencyResponse(BaseModel):
    total_comments: int
    total_nouns: int
    nouns: list[NounFrequencyItem]
