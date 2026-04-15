import logging

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from app.infrastructure.config.settings import get_settings
from app.infrastructure.langgraph.agent_state import MultiAgentState

logger = logging.getLogger(__name__)

_SYSTEM = """당신은 주식 분석 결과를 검토하는 리뷰어입니다.
Analyst가 작성한 분석 결과를 검토하고 품질을 평가합니다.

검토 기준:
1. 투자 추천(매수/매도) 표현이 포함되어 있지 않은가?
2. 분석 내용이 질문에 실질적으로 답하고 있는가?
3. 리스크 요인이 언급되어 있는가?

답변 형식 (반드시 준수):
PASS: [한 줄 피드백]
또는
FAIL: [개선이 필요한 이유]"""


def reviewer_node(state: MultiAgentState) -> dict:
    """Reviewer 노드: Analyst 결과를 검토하고 품질 통과 여부를 판정한다."""
    query = state["query"]
    analysis = state.get("analysis", "")
    logger.info("[Reviewer] start analysis=%s", analysis[:80])

    settings = get_settings()
    llm = ChatOpenAI(api_key=settings.openai_api_key, model=settings.openai_model)

    human_content = f"원본 질문: {query}\n\n분석 결과:\n{analysis}"
    messages = [
        SystemMessage(content=_SYSTEM),
        HumanMessage(content=human_content),
    ]

    try:
        response = llm.invoke(messages)
        verdict = response.content.strip()
        review_passed = verdict.upper().startswith("PASS")
        logger.info("[Reviewer] verdict=%s review_passed=%s", verdict[:80], review_passed)

        final_output = analysis if review_passed else None
        return {
            "review_passed": review_passed,
            "final_output": final_output,
            "messages": [*messages, response],
        }
    except Exception as e:
        logger.error("[Reviewer] failed: %s", e)
        raise RuntimeError(f"Reviewer 노드 실패: {e}") from e
