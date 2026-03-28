from collections import Counter

from app.domains.youtube.domain.service.synonym_table import SYNONYM_GROUPS


class KeywordSynonymService:
    """동의어/유사어를 대표 키워드로 통합하는 Domain Service."""

    def __init__(self) -> None:
        # 역방향 매핑: 동의어 → 대표 키워드
        self._mapping: dict[str, str] = {}
        for representative, synonyms in SYNONYM_GROUPS.items():
            for synonym in synonyms:
                self._mapping[synonym] = representative

    def normalize(self, noun: str) -> str:
        """명사를 대표 키워드로 변환한다. 매핑이 없으면 원본 반환."""
        return self._mapping.get(noun, noun)

    def merge(self, counter: Counter[str]) -> Counter[str]:
        """Counter의 키를 대표 키워드로 통합하고 빈도수를 합산한다."""
        merged: Counter[str] = Counter()
        for noun, count in counter.items():
            representative = self.normalize(noun)
            merged[representative] += count
        return merged
