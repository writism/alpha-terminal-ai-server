from typing import List

from pydantic import BaseModel


class CollectedVideoItem(BaseModel):
    video_id: str
    title: str
    channel_name: str
    published_at: str
    view_count: int
    thumbnail_url: str
    video_url: str


class CollectMarketVideoResponse(BaseModel):
    videos: List[CollectedVideoItem]
    saved_count: int
