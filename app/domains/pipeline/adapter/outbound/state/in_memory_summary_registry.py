"""SummaryRegistryPort 의 in-memory 어댑터.

Redis 미구성 시 폴백 또는 단위 테스트용. 단일 프로세스 내에서만 일관성 보장.
"""
from __future__ import annotations

from threading import RLock
from typing import Iterable, Optional

from app.domains.pipeline.application.response.stock_summary_response import StockSummaryResponse
from app.domains.pipeline.application.usecase.summary_registry_port import SummaryRegistryPort


class InMemorySummaryRegistry(SummaryRegistryPort):
    def __init__(self) -> None:
        self._data: dict[Optional[int], dict[str, StockSummaryResponse]] = {}
        self._lock = RLock()

    def put_all(
        self,
        account_id: Optional[int],
        summaries: Iterable[StockSummaryResponse],
    ) -> None:
        with self._lock:
            bucket = self._data.setdefault(account_id, {})
            for s in summaries:
                bucket[s.symbol] = s

    def get_all(self, account_id: Optional[int]) -> list[StockSummaryResponse]:
        with self._lock:
            return list(self._data.get(account_id, {}).values())
