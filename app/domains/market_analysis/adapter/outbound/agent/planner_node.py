import logging

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from app.infrastructure.config.settings import get_settings
from app.infrastructure.langgraph.agent_state import MultiAgentState

logger = logging.getLogger(__name__)

_SYSTEM = """당신은 주식 시장 분석 플래너입니다.
사용자의 질문을 받아 어떤 측면을 분석해야 할지 계획을 수립합니다.

규칙:
- 투자 추천, 매수/매도 의견은 절대 제공하지 않습니다.
- 분석 계획을 번호 목록으로 작성합니다 (3개 이내).
- 관련 종목명이 언급된 경우 명시합니다.
- 분석 관점(재무, 뉴스, 업종, 리스크 등)을 구체적으로 명시합니다."""


def planner_node(state: MultiAgentState) -> dict:
    """Planner 노드: 사용자 질문을 분석하고 분석 계획을 수립한다."""
    query = state["query"]
    logger.info("[Planner] start query=%s", query[:80])

    settings = get_settings()
    llm = ChatOpenAI(api_key=settings.openai_api_key, model=settings.openai_model)

    messages = [
        SystemMessage(content=_SYSTEM),
        HumanMessage(content=f"질문: {query}"),
    ]

    try:
        response = llm.invoke(messages)
        plan = response.content
        logger.info("[Planner] output plan=%s", plan[:120])
        return {
            "plan": plan,
            "messages": [*messages, response],
        }
    except Exception as e:
        logger.error("[Planner] failed: %s", e)
        raise RuntimeError(f"Planner 노드 실패: {e}") from e
