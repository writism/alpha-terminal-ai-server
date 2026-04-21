"""파이프라인 상태 저장소 팩토리.

- 환경 설정 `pipeline_state_redis_enabled` 가 True 이고 Redis PING 이 성공하면 Redis 어댑터.
- 그렇지 않으면 in-memory 어댑터로 폴백 (단일 프로세스 환경 호환).

프로세스당 한 번만 평가되어 싱글턴으로 공유된다.
"""
from __future__ import annotations

import logging

from app.domains.pipeline.application.usecase.progress_store_port import ProgressStorePort
from app.domains.pipeline.application.usecase.summary_registry_port import SummaryRegistryPort
from app.infrastructure.config.settings import get_settings

from .in_memory_progress_store import InMemoryProgressStore
from .in_memory_summary_registry import InMemorySummaryRegistry

logger = logging.getLogger(__name__)

_summary_registry: SummaryRegistryPort | None = None
_progress_store: ProgressStorePort | None = None


def _build_backends() -> tuple[SummaryRegistryPort, ProgressStorePort]:
    settings = get_settings()
    if settings.pipeline_state_redis_enabled:
        try:
            from app.infrastructure.cache.redis_client import redis_client

            redis_client.ping()
            from .redis_progress_store import RedisProgressStore
            from .redis_summary_registry import RedisSummaryRegistry

            logger.info("[pipeline-state] Redis 어댑터 사용")
            return RedisSummaryRegistry(redis_client), RedisProgressStore(redis_client)
        except Exception as e:
            logger.warning("[pipeline-state] Redis 연결 실패 → in-memory 폴백: %s", e)

    logger.info("[pipeline-state] in-memory 어댑터 사용")
    return InMemorySummaryRegistry(), InMemoryProgressStore()


def get_summary_registry() -> SummaryRegistryPort:
    global _summary_registry, _progress_store
    if _summary_registry is None:
        _summary_registry, _progress_store = _build_backends()
    return _summary_registry


def get_progress_store() -> ProgressStorePort:
    global _summary_registry, _progress_store
    if _progress_store is None:
        _summary_registry, _progress_store = _build_backends()
    return _progress_store
