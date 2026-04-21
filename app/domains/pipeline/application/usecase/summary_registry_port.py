"""파이프라인 실행 후 사용자별 최신 종목 요약을 저장/조회하기 위한 포트.

멀티 워커 배포에서도 일관성을 보장하기 위해 Redis 등 외부 저장소로 구현한다.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterable, Optional

from app.domains.pipeline.application.response.stock_summary_response import StockSummaryResponse


class SummaryRegistryPort(ABC):
    """사용자별 최신 종목 요약 저장소."""

    @abstractmethod
    def put_all(
        self,
        account_id: Optional[int],
        summaries: Iterable[StockSummaryResponse],
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_all(self, account_id: Optional[int]) -> list[StockSummaryResponse]:
        raise NotImplementedError
