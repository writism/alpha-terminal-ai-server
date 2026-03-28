from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class YouTubeVideo:
    video_id: str
    title: str
    thumbnail_url: str
    channel_name: str
    published_at: str
    video_url: str
    view_count: int = 0
    id: Optional[int] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
