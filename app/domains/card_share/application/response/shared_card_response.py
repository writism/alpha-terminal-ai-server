from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class SharedCardResponse(BaseModel):
    id: int
    symbol: str
    name: str
    summary: str
    tags: list[str]
    sentiment: str
    sentiment_score: float
    confidence: float
    source_type: str
    url: Optional[str]
    analyzed_at: datetime
    sharer_account_id: Optional[int]
    sharer_nickname: Optional[str]
    like_count: int
    comment_count: int
    created_at: datetime
    user_has_liked: bool = False


class SharedCardListResponse(BaseModel):
    cards: list[SharedCardResponse]
    total: int


class CardCommentResponse(BaseModel):
    id: int
    shared_card_id: int
    content: str
    author_nickname: str
    created_at: datetime


class CardCommentListResponse(BaseModel):
    comments: list[CardCommentResponse]


class LikeToggleResponse(BaseModel):
    liked: bool
    like_count: int
