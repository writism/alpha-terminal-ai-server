"""SummaryRegistryPort 의 Redis 어댑터.

키 구조:
    pipeline:summary:{account_id}  -> HASH { symbol: json(StockSummaryResponse) }
    account_id 가 None 이면 `anon` 으로 대체한다.

TTL: 기본 24시간. 장애/재시작 후 stale 데이터를 자동 정리.
"""
from __future__ import annotations

import json
import logging
from typing import Iterable, Optional

from app.domains.pipeline.application.response.stock_summary_response import StockSummaryResponse
from app.domains.pipeline.application.usecase.summary_registry_port import SummaryRegistryPort

logger = logging.getLogger(__name__)

_DEFAULT_TTL_SEC = 60 * 60 * 24  # 24h


class RedisSummaryRegistry(SummaryRegistryPort):
    def __init__(self, redis_client, ttl_sec: int = _DEFAULT_TTL_SEC) -> None:
        self._redis = redis_client
        self._ttl = ttl_sec

    @staticmethod
    def _key(account_id: Optional[int]) -> str:
        return f"pipeline:summary:{account_id if account_id is not None else 'anon'}"

    def put_all(
        self,
        account_id: Optional[int],
        summaries: Iterable[StockSummaryResponse],
    ) -> None:
        key = self._key(account_id)
        mapping: dict[str, str] = {}
        for s in summaries:
            mapping[s.symbol] = s.model_dump_json()
        if not mapping:
            return
        try:
            pipe = self._redis.pipeline()
            pipe.hset(key, mapping=mapping)
            pipe.expire(key, self._ttl)
            pipe.execute()
        except Exception as e:
            logger.warning("[RedisSummaryRegistry] put_all 실패: %s", e)

    def get_all(self, account_id: Optional[int]) -> list[StockSummaryResponse]:
        key = self._key(account_id)
        try:
            raw = self._redis.hgetall(key) or {}
        except Exception as e:
            logger.warning("[RedisSummaryRegistry] get_all 실패: %s", e)
            return []
        result: list[StockSummaryResponse] = []
        for _, value in raw.items():
            try:
                result.append(StockSummaryResponse.model_validate(json.loads(value)))
            except Exception:
                continue
        return result
