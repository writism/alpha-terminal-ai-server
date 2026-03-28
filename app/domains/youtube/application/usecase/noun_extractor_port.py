from abc import ABC, abstractmethod


class NounExtractorPort(ABC):
    @abstractmethod
    def extract_nouns(self, text: str) -> list[str]:
        """텍스트에서 명사를 추출하여 리스트로 반환한다."""
        ...
