from dataclasses import dataclass
from datetime import datetime


@dataclass
class RawArticle:
    id: str
    source_type: str
    source_name: str
    title: str
    body_text: str
    published_at: datetime
    symbol: str
    lang: str
