from app.domains.stock_theme.domain.service.recommendation_reason_prompt import (
    build_recommendation_reason_prompt,
)
from app.domains.stock_theme.domain.service.theme_match_service import ThemeMatchResult


def test_프롬프트에_매칭_키워드와_등록_테마가_포함된다():
    matches = [
        ThemeMatchResult(name="테스트", code="000001", matched_keywords=["AI"], relevance_score=0.5),
    ]
    theme_by_code = {"000001": ["AI", "클라우드"]}

    prompt = build_recommendation_reason_prompt(matches, theme_by_code)

    assert "000001" in prompt
    assert "AI" in prompt
    assert "클라우드" in prompt
    assert "JSON" in prompt
