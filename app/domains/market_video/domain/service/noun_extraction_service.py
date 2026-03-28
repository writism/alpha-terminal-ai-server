from collections import Counter
from typing import Dict, List


class NounExtractionService:
    """명사 필터링 및 빈도 집계 — 순수 Python 비즈니스 로직."""

    MIN_NOUN_LENGTH = 2  # 1글자 단독 명사 제외 (너무 일반적)

    def filter_nouns(self, nouns: List[str]) -> List[str]:
        """의미 없는 단어 제거."""
        return [n for n in nouns if len(n) >= self.MIN_NOUN_LENGTH]

    def count_frequencies(self, nouns: List[str]) -> Dict[str, int]:
        """빈도수 내림차순 정렬된 dict 반환."""
        return dict(Counter(nouns).most_common())
