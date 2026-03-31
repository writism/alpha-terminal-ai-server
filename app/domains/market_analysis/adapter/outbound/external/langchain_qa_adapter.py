from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from app.domains.market_analysis.application.usecase.langchain_qa_port import LangChainQAPort
from app.domains.market_analysis.domain.entity.analysis_answer import AnalysisAnswer

_OUT_OF_SCOPE_MARKER = "범위를 벗어납니다"

_SYSTEM_PROMPT = """당신은 주식 시장 분석 AI 어시스턴트입니다.
아래는 사용자의 관심종목과 각 종목의 테마 정보입니다:

{context}

위 관심종목 정보를 바탕으로 사용자의 질문에 답변하세요.
- 질문이 관심종목 또는 관련 테마와 무관할 경우 "죄송합니다. 해당 질문은 관심종목 분석 범위를 벗어납니다."라고 안내하세요.
- 투자 추천·매수·매도 의견은 제공하지 마세요.
- 답변은 한국어로 작성하세요."""


class LangChainQAAdapter(LangChainQAPort):
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        llm = ChatOpenAI(api_key=api_key, model=model)
        prompt = ChatPromptTemplate.from_messages([
            ("system", _SYSTEM_PROMPT),
            ("human", "{question}"),
        ])
        self._chain = prompt | llm | StrOutputParser()

    def ask(self, question: str, context: str) -> AnalysisAnswer:
        try:
            answer = self._chain.invoke({"context": context, "question": question})
            in_scope = _OUT_OF_SCOPE_MARKER not in answer
            return AnalysisAnswer(answer=answer, in_scope=in_scope)
        except Exception as e:
            return AnalysisAnswer(answer=f"분석 중 오류가 발생했습니다: {e}", in_scope=False)
