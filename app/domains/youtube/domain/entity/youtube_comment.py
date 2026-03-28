from dataclasses import dataclass


@dataclass
class YouTubeComment:
    comment_id: str
    video_id: str
    author_name: str
    text: str
    published_at: str
    like_count: int = 0
