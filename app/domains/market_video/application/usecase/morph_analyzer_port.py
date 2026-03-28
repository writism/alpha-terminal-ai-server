from abc import ABC, abstractmethod
from typing import List


class MorphAnalyzerPort(ABC):
    @abstractmethod
    def extract_nouns(self, text: str) -> List[str]:
        """텍스트에서 명사 목록을 반환한다."""
        pass
