from typing import List, Optional

from pydantic import BaseModel


class YoutubeVideoItem(BaseModel):
    title: str
    thumbnail_url: str
    channel_name: str
    published_at: str
    video_url: str


class YoutubeVideoListResponse(BaseModel):
    items: List[YoutubeVideoItem]
    next_page_token: Optional[str]
    prev_page_token: Optional[str]
    total_results: int
