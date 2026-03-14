from typing import Optional

from pydantic import BaseModel


class CreatePostRequest(BaseModel):
    title: str
    content: str
    author: Optional[str] = None
