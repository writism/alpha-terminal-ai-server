from datetime import datetime

from pydantic import BaseModel


class NormalizeRawArticleRequest(BaseModel):
    id: str
    source_type: str
    source_name: str
    title: str
    body_text: str
    published_at: datetime
    symbol: str
    lang: str = "ko"
