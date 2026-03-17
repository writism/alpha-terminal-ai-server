from datetime import datetime

from pydantic import BaseModel


class NormalizeRawArticleResponse(BaseModel):
    id: str
    raw_article_id: str
    stock_symbol: str
    source_type: str
    source_name: str
    title: str
    body: str
    category: str
    published_at: datetime
    lang: str
    content_quality: str
    normalized_at: datetime
    normalizer_version: str
