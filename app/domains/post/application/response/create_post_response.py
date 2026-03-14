from datetime import datetime

from pydantic import BaseModel


class CreatePostResponse(BaseModel):
    id: int
    title: str
    content: str
    author: str
    created_at: datetime
