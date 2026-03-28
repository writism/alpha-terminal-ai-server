from pydantic import BaseModel


class YouTubeVideoResponse(BaseModel):
    video_id: str
    title: str
    thumbnail_url: str
    channel_name: str
    published_at: str
    video_url: str
    view_count: int = 0


class YouTubeVideoListResponse(BaseModel):
    items: list[YouTubeVideoResponse]
    next_page_token: str | None = None
    prev_page_token: str | None = None
    total_results: int
