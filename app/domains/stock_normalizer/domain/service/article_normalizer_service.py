import re
import uuid
from datetime import datetime, timezone, timedelta

from app.domains.stock_normalizer.domain.entity.normalized_article import (
    NormalizedArticle, ArticleCategory, ContentQuality,
)
from app.domains.stock_normalizer.domain.entity.raw_article import RawArticle

KST = timezone(timedelta(hours=9))
NORMALIZER_VERSION = "normalizer-v1.0.0"

_CAPITAL_KEYWORDS = ["증자", "전환사채", "신주"]
_EARNINGS_KEYWORDS = ["실적", "영업이익", "매출"]


class ArticleNormalizerService:

    def normalize(self, raw: RawArticle) -> NormalizedArticle:
        title = self._clean_text(raw.title)
        body = self._clean_text(raw.body_text)
        return NormalizedArticle(
            id=str(uuid.uuid4()),
            raw_article_id=raw.id,
            stock_symbol=raw.symbol,
            source_type=raw.source_type,
            source_name=raw.source_name,
            title=title,
            body=body,
            category=self._classify_category(raw.source_type, title),
            published_at=self._normalize_datetime(raw.published_at),
            lang=raw.lang or "ko",
            content_quality=self._assess_quality(body),
            normalized_at=datetime.now(KST),
            normalizer_version=NORMALIZER_VERSION,
        )

    def _clean_text(self, text: str) -> str:
        if not text:
            return ""
        return re.sub(r'\s+', ' ', text.strip())

    def _classify_category(self, source_type: str, title: str) -> ArticleCategory:
        if source_type == "NEWS":
            return ArticleCategory.NEWS
        if source_type == "REPORT":
            return ArticleCategory.DISCLOSURE_OTHER
        if source_type == "DISCLOSURE":
            if any(kw in title for kw in _CAPITAL_KEYWORDS):
                return ArticleCategory.DISCLOSURE_CAPITAL
            if any(kw in title for kw in _EARNINGS_KEYWORDS):
                return ArticleCategory.DISCLOSURE_EARNINGS
            return ArticleCategory.DISCLOSURE_OTHER
        return ArticleCategory.UNKNOWN

    def _assess_quality(self, body: str) -> ContentQuality:
        if not body or len(body) < 10:
            return ContentQuality.INVALID
        if re.match(r'^[^a-zA-Z가-힣0-9]+$', body):
            return ContentQuality.INVALID
        return ContentQuality.VALID

    def _normalize_datetime(self, dt: datetime) -> datetime:
        if dt.tzinfo is None:
            return dt.replace(tzinfo=KST)
        return dt.astimezone(KST)
