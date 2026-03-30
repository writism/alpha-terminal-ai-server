from unittest.mock import MagicMock

from app.domains.stock_theme.domain.service.recommendation_reason_generation_service import (
    RecommendationReasonGenerationService,
)
from app.domains.stock_theme.domain.service.theme_match_service import ThemeMatchResult


def test_LLM이_JSON을_반환하면_코드_순서에_맞게_매핑():
    llm = MagicMock()
    llm.generate.return_value = (
        '[{"code":"000660","reason":"반도체 키워드와 테마가 맞아 추천됩니다."},'
        '{"code":"005930","reason":"AI 테마와 연결됩니다."}]'
    )
    service = RecommendationReasonGenerationService(llm)
    matches = [
        ThemeMatchResult(name="SK하이닉스", code="000660", matched_keywords=["반도체"], relevance_score=0.4),
        ThemeMatchResult(name="삼성전자", code="005930", matched_keywords=["AI"], relevance_score=0.3),
    ]
    theme_by_code = {"000660": ["반도체", "메모리"], "005930": ["AI", "전자"]}

    reasons = service.build_reasons(matches, theme_by_code)

    assert reasons == [
        "반도체 키워드와 테마가 맞아 추천됩니다.",
        "AI 테마와 연결됩니다.",
    ]
    llm.generate.assert_called_once()


def test_LLM_실패_시_폴백_문장():
    llm = MagicMock()
    llm.generate.side_effect = RuntimeError("OPENAI_API_KEY is not configured")
    service = RecommendationReasonGenerationService(llm)
    matches = [
        ThemeMatchResult(name="SK하이닉스", code="000660", matched_keywords=["반도체"], relevance_score=0.4),
    ]
    theme_by_code = {"000660": ["반도체"]}

    reasons = service.build_reasons(matches, theme_by_code)

    assert len(reasons) == 1
    assert "000660" in reasons[0]
    assert "반도체" in reasons[0]


def test_코드펜스로_감싼_JSON도_파싱한다():
    llm = MagicMock()
    llm.generate.return_value = '```json\n[{"code":"000660","reason":"펜스 안 이유"}]\n```'
    service = RecommendationReasonGenerationService(llm)
    matches = [
        ThemeMatchResult(name="SK하이닉스", code="000660", matched_keywords=["반도체"], relevance_score=0.4),
    ]
    reasons = service.build_reasons(matches, {"000660": ["반도체"]})
    assert reasons == ["펜스 안 이유"]


def test_JSON_파싱_실패_시_해당_종목만_폴백():
    llm = MagicMock()
    llm.generate.return_value = "not json"
    service = RecommendationReasonGenerationService(llm)
    matches = [
        ThemeMatchResult(name="SK하이닉스", code="000660", matched_keywords=["반도체"], relevance_score=0.4),
    ]
    theme_by_code = {"000660": ["반도체"]}

    reasons = service.build_reasons(matches, theme_by_code)

    assert "000660" in reasons[0]
    assert "반도체" in reasons[0]
