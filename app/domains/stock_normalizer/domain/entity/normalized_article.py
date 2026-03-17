from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class ArticleCategory(str, Enum):
    DISCLOSURE_CAPITAL = "DISCLOSURE_CAPITAL"
    DISCLOSURE_EARNINGS = "DISCLOSURE_EARNINGS"
    DISCLOSURE_OTHER = "DISCLOSURE_OTHER"
    NEWS = "NEWS"
    UNKNOWN = "UNKNOWN"


class ContentQuality(str, Enum):
    VALID = "VALID"
    INVALID = "INVALID"


@dataclass
class NormalizedArticle:
    id: str
    raw_article_id: str
    stock_symbol: str
    source_type: str
    source_name: str
    title: str
    body: str
    category: ArticleCategory
    published_at: datetime
    lang: str
    content_quality: ContentQuality
    normalized_at: datetime
    normalizer_version: str
