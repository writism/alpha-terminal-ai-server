"""ProgressStorePort 의 Redis 어댑터.

키: pipeline:progress:{account_id} -> LIST of messages (RPUSH / LRANGE)
TTL: 기본 1시간 (파이프라인 수행 시간 커버).
"""
from __future__ import annotations

import logging
from typing import Optional

from app.domains.pipeline.application.usecase.progress_store_port import ProgressStorePort

logger = logging.getLogger(__name__)

_DEFAULT_TTL_SEC = 60 * 60  # 1h


class RedisProgressStore(ProgressStorePort):
    def __init__(self, redis_client, ttl_sec: int = _DEFAULT_TTL_SEC) -> None:
        self._redis = redis_client
        self._ttl = ttl_sec

    @staticmethod
    def _key(account_id: Optional[int]) -> str:
        return f"pipeline:progress:{account_id if account_id is not None else 'anon'}"

    def append(self, account_id: Optional[int], message: str) -> None:
        key = self._key(account_id)
        try:
            pipe = self._redis.pipeline()
            pipe.rpush(key, message)
            pipe.expire(key, self._ttl)
            pipe.execute()
        except Exception as e:
            logger.warning("[RedisProgressStore] append 실패: %s", e)

    def read_all(self, account_id: Optional[int]) -> list[str]:
        key = self._key(account_id)
        try:
            return list(self._redis.lrange(key, 0, -1) or [])
        except Exception as e:
            logger.warning("[RedisProgressStore] read_all 실패: %s", e)
            return []

    def clear(self, account_id: Optional[int]) -> None:
        try:
            self._redis.delete(self._key(account_id))
        except Exception as e:
            logger.warning("[RedisProgressStore] clear 실패: %s", e)
