"""ProgressStorePort 의 in-memory 어댑터."""
from __future__ import annotations

from threading import RLock
from typing import Optional

from app.domains.pipeline.application.usecase.progress_store_port import ProgressStorePort


class InMemoryProgressStore(ProgressStorePort):
    def __init__(self) -> None:
        self._data: dict[Optional[int], list[str]] = {}
        self._lock = RLock()

    def append(self, account_id: Optional[int], message: str) -> None:
        with self._lock:
            self._data.setdefault(account_id, []).append(message)

    def read_all(self, account_id: Optional[int]) -> list[str]:
        with self._lock:
            return list(self._data.get(account_id, []))

    def clear(self, account_id: Optional[int]) -> None:
        with self._lock:
            self._data.pop(account_id, None)
