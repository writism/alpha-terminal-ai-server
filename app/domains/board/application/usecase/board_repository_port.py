from abc import ABC, abstractmethod
from typing import List, Optional

from app.domains.board.domain.entity.board import Board


class BoardRepositoryPort(ABC):
    @abstractmethod
    def save(self, board: Board) -> Board:
        pass

    @abstractmethod
    def find_by_id(self, board_id: int) -> Optional[Board]:
        pass

    @abstractmethod
    def find_paginated(self, page: int, size: int) -> List[Board]:
        pass

    @abstractmethod
    def count_total(self) -> int:
        pass
