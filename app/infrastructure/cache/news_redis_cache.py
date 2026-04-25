"""뉴스 검색 결과 Redis 캐시 — SerpApi 반복 호출 비용 절감 (TTL 5분)."""

from __future__ import annotations

import json
import logging
from typing import Optional

import redis

logger = logging.getLogger(__name__)

_KEY_PREFIX = "alphadesk:news:search:v1:"
_TTL_SEC = 300  # 5분


def _news_cache_key(keyword: str, market: Optional[str], page: int, page_size: int) -> str:
    market_part = market or "all"
    return f"{_KEY_PREFIX}{market_part}:{page}:{page_size}:{keyword}"


def get_news_cache(
    client: redis.Redis,
    keyword: str,
    market: Optional[str],
    page: int,
    page_size: int,
) -> Optional[dict]:
    try:
        raw = client.get(_news_cache_key(keyword, market, page, page_size))
        if raw is None:
            return None
        return json.loads(raw)
    except (redis.RedisError, json.JSONDecodeError) as e:
        logger.debug("[NewsRedisCache] get failed: %s", type(e).__name__)
        return None


def set_news_cache(
    client: redis.Redis,
    keyword: str,
    market: Optional[str],
    page: int,
    page_size: int,
    data: dict,
) -> None:
    try:
        client.setex(
            _news_cache_key(keyword, market, page, page_size),
            _TTL_SEC,
            json.dumps(data, ensure_ascii=False),
        )
    except (redis.RedisError, TypeError, ValueError) as e:
        logger.debug("[NewsRedisCache] set failed: %s", type(e).__name__)
