"""Synthesis Agent 노드 — investment_verdict 기반 최종 응답을 종합한다.

응답 구조 (2~4 문단):
    결론 한 줄 (verdict 한국어 표현 + confidence 수준)
    → 긍정 근거 요약 (investment_verdict.reasons.positive 기반)
    → 부정 근거 / 리스크 요약 (reasons.negative + risk_factors 기반)
    → 면책 문구 (자동 부착)

규칙:
    - direction / confidence / verdict 는 절대 재계산하지 않는다.
    - LLM 은 reasons 를 자연어 문장으로 풀어 쓰는 역할만 수행한다 (새 근거 생성 금지).
    - investment_verdict 누락 시 analysis 텍스트로 fallback (참고용 명시).
    - hold + confidence ≤ 0.3 이면 신호 부족 안내 문구를 삽입한다.
"""
from typing import Optional

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from app.domains.investment.adapter.outbound.agent.investment_agent_state import (
    InvestmentAgentState,
    NEXT_END,
)
from app.domains.investment.adapter.outbound.agent.log_context import aemit
from app.infrastructure.config.settings import get_settings

# ---------------------------------------------------------------------------
# 상수
# ---------------------------------------------------------------------------

_VERDICT_KR: dict[str, str] = {
    "buy":  "매수",
    "hold": "보유",
    "sell": "매도",
}

_DISCLAIMER = (
    "\n\n※ 면책 문구: 본 응답은 투자 권유가 아닌 정보 제공을 목적으로 합니다. "
    "투자 결정은 본인의 판단과 책임 하에 이루어져야 하며, "
    "본 정보는 투자 결과를 보장하지 않습니다."
)

_SIGNAL_SHORTAGE_NOTE = (
    "\n\n⚠ 참고: 분석에 활용된 신호 데이터가 충분하지 않아 "
    "보수적 기본값(보유)이 적용되었습니다. "
    "추가 데이터 수집 후 재분석을 권장합니다."
)

_FALLBACK_HEADER = "※ 이 응답은 구조화 투자 판단이 누락되어 참고용 분석 결과를 기반으로 생성되었습니다.\n\n"

# confidence → 확신 수준 라벨
_CONFIDENCE_LEVELS = [
    (0.7, "높은 확신"),
    (0.4, "일정 수준의 가능성"),
    (0.0, "불확실성이 높은 상태"),
]


def _confidence_label(confidence: float) -> str:
    for threshold, label in _CONFIDENCE_LEVELS:
        if confidence >= threshold:
            return label
    return "불확실성이 높은 상태"


# ---------------------------------------------------------------------------
# 프롬프트 빌더
# ---------------------------------------------------------------------------

def _build_system_prompt() -> str:
    return (
        "당신은 투자 정보 종합 에이전트입니다.\n"
        "아래 구조화된 투자 판단 결과를 바탕으로 사용자 친화적인 한국어 응답을 작성하세요.\n\n"
        "작성 규칙:\n"
        "- verdict(결론)를 첫 문단에 자연스럽게 녹여 쓰세요. 완곡하거나 모호하게 표현하지 마세요.\n"
        "- reasons.positive / reasons.negative / risk_factors 에 제시된 내용을 근거로 사용하세요.\n"
        "- direction, confidence, verdict 같은 내부 필드명과 수치를 응답에 그대로 출력하지 마세요.\n"
        "  예: 'direction: neutral', 'confidence: 0.300' 같은 표현 금지.\n"
        "- 2~4개 문단으로 구성하세요: 결론 → 긍정 근거 → 부정/리스크 → (필요시 추가)\n"
        "- 한국어 자연스러운 서술형으로 작성하세요.\n"
        "- 응답 말미에 면책 문구가 자동으로 추가되므로 직접 쓰지 마세요."
    )


def _build_human_prompt(
    query: str,
    company: Optional[str],
    verdict_kr: str,
    confidence: float,
    conf_label: str,
    direction: str,
    positive_reasons: list,
    negative_reasons: list,
    risk_factors: list,
    is_low_confidence_hold: bool,
) -> str:
    low_conf_note = (
        "\n⚠ 주의: 신호 부족으로 인한 보수적 판단입니다. 이 점을 응답에 명확히 반영하세요."
        if is_low_confidence_hold else ""
    )

    return (
        f"사용자 질문: {query}\n"
        f"종목: {company or '미지정'}\n\n"
        f"=== 투자 판단 결과 (변경 금지) ===\n"
        f"결론     : {verdict_kr}\n"
        f"방향성   : {'상승' if direction == 'bullish' else '하락' if direction == 'bearish' else '중립'}\n"
        f"확신도   : {conf_label}\n\n"
        f"=== 긍정 근거 (이 내용만 사용) ===\n"
        + ("\n".join(f"- {r}" for r in positive_reasons) or "- 없음") + "\n\n"
        f"=== 부정 근거 (이 내용만 사용) ===\n"
        + ("\n".join(f"- {r}" for r in negative_reasons) or "- 없음") + "\n\n"
        f"=== 리스크 요인 (이 내용만 사용) ===\n"
        + ("\n".join(f"- {r}" for r in risk_factors) or "- 없음")
        + f"\n{low_conf_note}\n\n"
        f"위 정보를 바탕으로 응답을 작성하세요. verdict({verdict_kr})를 첫 문단에 명확히 표현하세요."
    )


# ---------------------------------------------------------------------------
# Synthesis 노드
# ---------------------------------------------------------------------------

async def synthesis_node(state: InvestmentAgentState) -> dict:
    """Synthesis 노드: investment_verdict 기반 최종 응답을 생성한다.

    investment_verdict 누락 시 analysis 텍스트로 fallback.
    """
    query = state["query"]
    parsed_query = state.get("parsed_query") or {}
    company: Optional[str] = parsed_query.get("company")
    investment_verdict: Optional[dict] = state.get("investment_verdict")
    analysis: Optional[str] = state.get("analysis", "")

    await aemit(f"[Synthesis] ▶ 시작")
    await aemit(
        f"[Synthesis]   investment_verdict={'있음' if investment_verdict else '없음(fallback)'} | "
        f"company={company}"
    )

    settings = get_settings()
    llm = ChatOpenAI(api_key=settings.openai_api_key, model=settings.openai_model, temperature=0.3)

    # -------------------------------------------------------------------------
    # Case A: investment_verdict 있음 → 구조화 판단 기반 응답
    # -------------------------------------------------------------------------
    if investment_verdict:
        verdict_raw: str = investment_verdict.get("verdict", "hold")
        direction: str = investment_verdict.get("direction", "neutral")
        confidence: float = float(investment_verdict.get("confidence", 0.3))
        reasons: dict = investment_verdict.get("reasons", {})
        risk_factors: list = investment_verdict.get("risk_factors", [])

        verdict_kr = _VERDICT_KR.get(verdict_raw, "보유")
        conf_label = _confidence_label(confidence)
        positive_reasons: list = reasons.get("positive", [])
        negative_reasons: list = reasons.get("negative", [])
        is_low_confidence_hold = (verdict_raw == "hold" and confidence <= 0.3)

        print(f"[Synthesis] === 투자 판단 입력 ===")
        print(f"[Synthesis]   verdict    : {verdict_raw} → {verdict_kr}")
        print(f"[Synthesis]   direction  : {direction}")
        print(f"[Synthesis]   confidence : {confidence:.3f} ({conf_label})")
        print(f"[Synthesis]   positive   : {positive_reasons}")
        print(f"[Synthesis]   negative   : {negative_reasons}")
        print(f"[Synthesis]   risks      : {risk_factors}")
        print(f"[Synthesis]   low_conf_hold: {is_low_confidence_hold}")

        system_msg = _build_system_prompt()
        human_msg = _build_human_prompt(
            query=query,
            company=company,
            verdict_kr=verdict_kr,
            confidence=confidence,
            conf_label=conf_label,
            direction=direction,
            positive_reasons=positive_reasons,
            negative_reasons=negative_reasons,
            risk_factors=risk_factors,
            is_low_confidence_hold=is_low_confidence_hold,
        )

        await aemit(f"[Synthesis] → LLM 응답 생성 중 (verdict={verdict_kr}, conf={confidence:.3f})...")

        if is_low_confidence_hold:
            # 신호 부족 → LLM 일반 지식 기반 직접 답변
            general_system = (
                "당신은 투자 정보 분석 전문가입니다.\n"
                "실시간 데이터가 충분하지 않은 상황에서, 질문에 대해 일반적인 시장 지식과 "
                "해당 기업·산업에 대한 맥락을 바탕으로 균형 잡힌 분석을 제공하세요.\n\n"
                "작성 규칙:\n"
                "- 질문에 직접적으로 답하세요. '데이터 없음'으로 회피하지 마세요.\n"
                "- 긍정적 가능성과 부정적 리스크를 모두 언급하세요.\n"
                "- 실시간 데이터가 아닌 일반 지식 기반임을 자연스럽게 한 줄로만 안내하세요.\n"
                "- 수치 예측은 단정하지 말고 조건부로 서술하세요.\n"
                "- 3~4 문단, 자연스러운 한국어 서술형으로 작성하세요.\n"
                "- 응답 말미에 면책 문구가 자동으로 추가되므로 직접 쓰지 마세요."
            )
            general_human = f"사용자 질문: {query}\n종목: {company or '미지정'}\n\n위 질문에 답하세요."
            messages = [SystemMessage(content=general_system), HumanMessage(content=general_human)]
        else:
            messages = [SystemMessage(content=system_msg), HumanMessage(content=human_msg)]

        response = await llm.ainvoke(messages)
        final_answer = response.content.strip() + _DISCLAIMER

    # -------------------------------------------------------------------------
    # Case B: investment_verdict 없음 → analysis 텍스트 fallback
    # -------------------------------------------------------------------------
    else:
        await aemit(f"[Synthesis] ⚠ investment_verdict 없음 → analysis fallback 사용")
        print(f"[Synthesis] ⚠ FALLBACK 경로: analysis 텍스트 기반 응답 생성")

        if not analysis:
            final_answer = (
                _FALLBACK_HEADER
                + "분석 결과가 없어 응답을 생성할 수 없습니다."
                + _DISCLAIMER
            )
        else:
            fallback_system = (
                "당신은 투자 정보 종합 에이전트입니다.\n"
                "아래 분석 결과를 사용자 친화적으로 요약하세요.\n"
                "이 응답은 참고용 분석 결과임을 첫 줄에 명시하세요.\n"
                "투자 추천(매수/매도) 표현은 사용하지 마세요."
            )
            fallback_human = (
                f"사용자 질문: {query}\n\n"
                f"분석 결과:\n{analysis}\n\n"
                "참고용 분석 결과임을 명시하고, 위 내용을 요약하세요."
            )
            messages = [
                SystemMessage(content=fallback_system),
                HumanMessage(content=fallback_human),
            ]
            response = await llm.ainvoke(messages)
            final_answer = _FALLBACK_HEADER + response.content.strip() + _DISCLAIMER

    # -------------------------------------------------------------------------
    # pretty-print 결과 확인
    # -------------------------------------------------------------------------
    preview = final_answer[:200].replace("\n", " ")
    print(f"[Synthesis] ===== 최종 응답 =====")
    if investment_verdict:
        print(f"[Synthesis]   verdict    : {_VERDICT_KR.get(investment_verdict.get('verdict','hold'), '보유')}")
        print(f"[Synthesis]   confidence : {float(investment_verdict.get('confidence', 0.0)):.3f}")
    else:
        print(f"[Synthesis]   경로       : fallback (analysis)")
    print(f"[Synthesis]   본문 미리보기: {preview}...")
    print(f"[Synthesis]   전체 길이   : {len(final_answer)}자")
    print(f"[Synthesis] ========================")

    await aemit(f"[Synthesis] ◀ 완료 | {len(final_answer)}자 생성")

    return {
        "final_answer": final_answer,
        "next_agent": NEXT_END,
    }
