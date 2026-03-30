"""BL-BE-51: 추천 이유 배치 생성용 프롬프트 템플릿."""

from collections.abc import Mapping, Sequence

from app.domains.stock_theme.domain.service.theme_match_service import ThemeMatchResult

_SYSTEM_DIRECTIVE = """당신은 주식 앱의 추천 설명을 작성하는 어시스턴트입니다.
아래 종목들은 '사용자 댓글/키워드 분석에서 나온 용어'와 '각 종목에 DB에 등록된 테마 태그'가 겹쳐 추천된 결과입니다.
각 종목마다 1~3문장의 한국어로, 어떤 키워드(분석에서 잡힌 용어)가 종목의 어떤 테마 맥락과 맞물려 이 종목이 추천되었는지 자연스럽게 설명하세요.
전문 용어는 필요 시 짧게 풀어 쓰고, 과장·확정적 수익 약속은 하지 마세요.
"""

_JSON_RULE = """
반드시 아래 형식의 JSON 배열만 출력하세요. 앞뒤로 설명 문장이나 마크다운 코드블록을 붙이지 마세요.
각 객체의 code는 입력과 동일한 종목코드여야 합니다.
[{"code":"종목코드","reason":"추천 이유 문장"}, ...]
"""


def build_recommendation_reason_prompt(
    matches: Sequence[ThemeMatchResult],
    theme_by_code: Mapping[str, Sequence[str]],
) -> str:
    rows: list[str] = []
    for i, m in enumerate(matches, start=1):
        all_themes = list(theme_by_code.get(m.code, ()))
        themes_display = ", ".join(all_themes) if all_themes else "(등록 테마 없음)"
        matched_display = ", ".join(m.matched_keywords) if m.matched_keywords else "(없음)"
        rows.append(
            f"{i}. {m.name} ({m.code}) — 매칭된 키워드(분석·테마 교집합): [{matched_display}] "
            f"— 종목 등록 테마 전체: [{themes_display}] — 관련성 점수: {m.relevance_score}"
        )

    body = "\n".join(rows)
    return f"{_SYSTEM_DIRECTIVE}\n추천 후보:\n{body}\n{_JSON_RULE}"
