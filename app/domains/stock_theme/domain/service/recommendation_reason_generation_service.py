import json
import logging
import re
from collections.abc import Mapping, Sequence

from app.domains.llm.application.usecase.text_generation_port import TextGenerationPort
from app.domains.stock_theme.domain.service.recommendation_reason_prompt import (
    build_recommendation_reason_prompt,
)
from app.domains.stock_theme.domain.service.theme_match_service import ThemeMatchResult

logger = logging.getLogger(__name__)


def _strip_code_fence(text: str) -> str:
    t = text.strip()
    m = re.search(r"```(?:json)?\s*([\s\S]*?)```", t, re.IGNORECASE)
    if m:
        return m.group(1).strip()
    return t


def _parse_reason_map(raw: str) -> dict[str, str]:
    s = _strip_code_fence(raw)
    start = s.find("[")
    end = s.rfind("]")
    if start == -1 or end <= start:
        return {}
    chunk = s[start : end + 1]
    try:
        data = json.loads(chunk)
    except json.JSONDecodeError:
        return {}
    if not isinstance(data, list):
        return {}
    out: dict[str, str] = {}
    for item in data:
        if not isinstance(item, dict):
            continue
        code = item.get("code")
        reason = item.get("reason")
        if isinstance(code, str) and isinstance(reason, str) and reason.strip():
            out[code.strip()] = reason.strip()
    return out


def _fallback_reason(match: ThemeMatchResult, theme_by_code: Mapping[str, Sequence[str]]) -> str:
    themes = list(theme_by_code.get(match.code, ()))
    themes_part = ", ".join(themes) if themes else "등록된 테마"
    kw_part = ", ".join(match.matched_keywords) if match.matched_keywords else "키워드"
    return (
        f"{match.name}({match.code})은(는) 분석에서 도출된 「{kw_part}」가 "
        f"종목에 등록된 테마({themes_part})와 연결되어 추천 목록에 포함되었습니다. "
        f"(관련성 점수 {match.relevance_score:.4f})"
    )


class RecommendationReasonGenerationService:
    """BL-BE-51: 매칭 결과를 바탕으로 종목별 추천 이유 문장을 생성한다."""

    def __init__(self, llm: TextGenerationPort) -> None:
        self._llm = llm

    def build_reasons(
        self,
        matches: Sequence[ThemeMatchResult],
        theme_by_code: Mapping[str, Sequence[str]],
    ) -> list[str]:
        if not matches:
            return []

        prompt = build_recommendation_reason_prompt(matches, theme_by_code)
        raw = ""
        try:
            raw = self._llm.generate(prompt)
        except RuntimeError as e:
            logger.warning("추천 이유 LLM 호출 생략(설정/API): %s", e)
            return [_fallback_reason(m, theme_by_code) for m in matches]
        except Exception:
            logger.exception("추천 이유 LLM 호출 실패")
            return [_fallback_reason(m, theme_by_code) for m in matches]

        reason_by_code = _parse_reason_map(raw)
        ordered: list[str] = []
        for m in matches:
            text = reason_by_code.get(m.code, "").strip()
            if not text:
                text = _fallback_reason(m, theme_by_code)
            ordered.append(text)
        return ordered
