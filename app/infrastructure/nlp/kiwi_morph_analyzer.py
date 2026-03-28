from typing import List

from kiwipiepy import Kiwi

from app.domains.market_video.application.usecase.morph_analyzer_port import MorphAnalyzerPort

# 모델 로딩이 무거우므로 모듈 레벨에서 한 번만 초기화
_kiwi = Kiwi()


class KiwiMorphAnalyzer(MorphAnalyzerPort):
    # 일반명사(NNG), 고유명사(NNP)만 추출 — 키워드 추출 목적에 적합
    _NOUN_TAGS = {"NNG", "NNP"}

    def extract_nouns(self, text: str) -> List[str]:
        tokens = _kiwi.tokenize(text)
        return [t.form for t in tokens if t.tag in self._NOUN_TAGS]
