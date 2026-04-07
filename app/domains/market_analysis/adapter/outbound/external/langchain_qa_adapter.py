from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from app.domains.market_analysis.application.usecase.question_analyzer_port import QuestionAnalyzerPort

_SYSTEM_PROMPT = """\
당신은 Alpha-Desk 주식 테마 분석 도우미입니다.
아래에 제공된 종목/테마 데이터만을 근거로 사용자의 질문에 사실 기반으로 답변하세요.

{context}

[답변 규칙]
1. 위 데이터에 포함된 종목 및 테마와 관련된 질문에만 답변하세요.
2. 투자 추천, 매수/매도 의견은 절대 제시하지 마세요. 사실 기반 정보 요약만 제공하세요.
3. 위 데이터와 관련 없는 질문(주식/테마 분석과 무관한 질문)은 반드시 다음 문장으로만 응답하세요:
   "이 서비스는 Alpha-Desk에 등록된 주식 테마 분석을 위한 서비스입니다. 해당 질문은 제공 가능한 범위를 벗어납니다."
4. 답변은 한국어로 작성하세요.\
"""


class LangchainQaAdapter(QuestionAnalyzerPort):
    """LangChain LCEL 체인을 사용하여 종목/테마 컨텍스트 기반 질문 답변을 생성한다."""

    def __init__(self, api_key: str, model: str):
        llm = ChatOpenAI(model=model, api_key=api_key)
        prompt = ChatPromptTemplate.from_messages([
            ("system", _SYSTEM_PROMPT),
            ("human", "{question}"),
        ])
        self._chain = prompt | llm | StrOutputParser()

    async def analyze(self, context: str, question: str) -> str:
        return await self._chain.ainvoke({"context": context, "question": question})
