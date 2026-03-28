from dataclasses import dataclass
from datetime import datetime


@dataclass
class VideoComment:
    comment_id: str
    video_id: str
    author: str
    content: str
    published_at: datetime
    like_count: int
