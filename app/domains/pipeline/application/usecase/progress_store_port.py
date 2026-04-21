"""파이프라인 진행 메시지 저장소 포트.

멀티 워커 배포에서도 일관된 진행 상태를 조회할 수 있도록 Redis 등 외부 저장소로 구현한다.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional


class ProgressStorePort(ABC):
    """사용자별 파이프라인 진행 로그 저장소."""

    @abstractmethod
    def append(self, account_id: Optional[int], message: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def read_all(self, account_id: Optional[int]) -> list[str]:
        raise NotImplementedError

    @abstractmethod
    def clear(self, account_id: Optional[int]) -> None:
        raise NotImplementedError
