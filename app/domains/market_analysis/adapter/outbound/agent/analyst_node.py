import logging

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from app.infrastructure.config.settings import get_settings
from app.infrastructure.langgraph.agent_state import MultiAgentState

logger = logging.getLogger(__name__)

_SYSTEM = """당신은 주식 시장 분석가입니다.
Planner가 수립한 분석 계획을 바탕으로 사용자의 질문에 대한 분석을 수행합니다.

규칙:
- 투자 추천, 매수/매도 의견은 절대 제공하지 않습니다.
- 분석은 사실 기반으로 작성하며, 불확실한 내용은 명시합니다.
- 리스크 요인이 있으면 반드시 언급합니다.
- 분석 결과는 명확하고 간결하게 작성합니다 (5문장 이내)."""


def analyst_node(state: MultiAgentState) -> dict:
    """Analyst 노드: Planner의 계획을 바탕으로 실제 분석을 수행한다."""
    query = state["query"]
    plan = state.get("plan", "")
    retry_count = state.get("retry_count", 0)
    logger.info("[Analyst] start query=%s retry=%s", query[:80], retry_count)

    settings = get_settings()
    llm = ChatOpenAI(api_key=settings.openai_api_key, model=settings.openai_model)

    human_content = f"질문: {query}\n\n분석 계획:\n{plan}"
    messages = [
        SystemMessage(content=_SYSTEM),
        HumanMessage(content=human_content),
    ]

    try:
        response = llm.invoke(messages)
        analysis = response.content
        logger.info("[Analyst] output analysis=%s", analysis[:120])
        return {
            "analysis": analysis,
            "retry_count": retry_count + 1,
            "messages": [*messages, response],
        }
    except Exception as e:
        logger.error("[Analyst] failed: %s", e)
        raise RuntimeError(f"Analyst 노드 실패: {e}") from e
