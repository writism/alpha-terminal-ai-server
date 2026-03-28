from kiwipiepy import Kiwi

from app.domains.youtube.application.usecase.noun_extractor_port import NounExtractorPort

# 모듈 레벨 싱글턴 (모델 로딩은 한 번만)
_kiwi = Kiwi()


class KiwiNounExtractor(NounExtractorPort):
    def extract_nouns(self, text: str) -> list[str]:
        """kiwipiepy로 명사(NNG, NNP)를 추출한다."""
        tokens = _kiwi.tokenize(text)
        return [t.form for t in tokens if t.tag in ("NNG", "NNP") and len(t.form) > 1]
