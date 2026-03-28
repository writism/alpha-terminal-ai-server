from typing import List

from pydantic import BaseModel


class VideoCommentItem(BaseModel):
    comment_id: str
    author: str
    content: str
    published_at: str
    like_count: int


class VideoCommentGroup(BaseModel):
    video_id: str
    comments: List[VideoCommentItem]


class CollectVideoCommentsResponse(BaseModel):
    video_comments: List[VideoCommentGroup]
    total_comment_count: int
