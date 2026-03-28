from collections import Counter

from app.domains.youtube.application.response.noun_frequency_response import (
    NounFrequencyItem,
    NounFrequencyResponse,
)
from app.domains.youtube.application.usecase.noun_extractor_port import NounExtractorPort
from app.domains.youtube.application.usecase.youtube_comment_repository_port import YouTubeCommentRepositoryPort
from app.domains.youtube.domain.service.keyword_synonym_service import KeywordSynonymService


class ExtractNounsUseCase:
    def __init__(
        self,
        repository: YouTubeCommentRepositoryPort,
        noun_extractor: NounExtractorPort,
    ):
        self._repository = repository
        self._noun_extractor = noun_extractor
        self._synonym_service = KeywordSynonymService()

    def execute(self, top_n: int = 30) -> NounFrequencyResponse:
        comments = self._repository.find_all()

        counter: Counter[str] = Counter()
        for comment in comments:
            nouns = self._noun_extractor.extract_nouns(comment.text)
            counter.update(nouns)

        # 동의어 통합
        merged = self._synonym_service.merge(counter)

        ranked = [
            NounFrequencyItem(noun=noun, count=count)
            for noun, count in merged.most_common(top_n)
        ]

        return NounFrequencyResponse(
            total_comments=len(comments),
            total_nouns=len(merged),
            nouns=ranked,
        )
