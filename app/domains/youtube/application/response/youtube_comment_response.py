from pydantic import BaseModel


class YouTubeCommentResponse(BaseModel):
    comment_id: str
    video_id: str
    author_name: str
    text: str
    published_at: str
    like_count: int = 0


class YouTubeCommentListResponse(BaseModel):
    items: list[YouTubeCommentResponse]
    video_id: str
    total_collected: int
