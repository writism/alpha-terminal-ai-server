from typing import List

from pydantic import BaseModel


class NounFrequencyItem(BaseModel):
    noun: str
    count: int


class NounFrequencyResponse(BaseModel):
    keywords: List[NounFrequencyItem]
    total_noun_count: int
    analyzed_video_count: int
