from typing import Optional

from fastapi import APIRouter, Cookie, Depends, HTTPException
from sqlalchemy.orm import Session

from app.domains.auth.adapter.outbound.in_memory.redis_session_adapter import RedisSessionAdapter
from app.domains.market_analysis.adapter.outbound.external.langchain_qa_adapter import LangchainQaAdapter
from app.domains.market_analysis.adapter.outbound.persistence.stock_theme_data_adapter import StockThemeDataAdapter
from app.domains.market_analysis.application.request.analyze_question_request import AnalyzeQuestionRequest
from app.domains.market_analysis.application.response.analyze_question_response import AnalyzeQuestionResponse
from app.domains.market_analysis.application.usecase.analyze_question_usecase import AnalyzeQuestionUseCase
from app.domains.market_analysis.domain.service.market_context_builder_service import MarketContextBuilderService
from app.infrastructure.cache.redis_client import redis_client
from app.infrastructure.config.settings import get_settings
from app.infrastructure.database.session import get_db

router = APIRouter(prefix="/market-analysis", tags=["market-analysis"])

_session_adapter = RedisSessionAdapter(redis_client)


@router.post("/analyze", response_model=AnalyzeQuestionResponse)
async def analyze_question(
    request: AnalyzeQuestionRequest,
    user_token: Optional[str] = Cookie(default=None),
    db: Session = Depends(get_db),
):
    """DB에 저장된 종목/테마 데이터를 LangChain 컨텍스트로 주입하여 사용자 질문에 답변한다. `user_token` 쿠키 필요."""
    if not user_token:
        raise HTTPException(status_code=401, detail="인증이 필요합니다.")
    if _session_adapter.find_by_token(user_token) is None:
        raise HTTPException(status_code=401, detail="세션이 만료되었거나 유효하지 않습니다.")

    settings = get_settings()
    stock_data_port = StockThemeDataAdapter(db)
    question_analyzer_port = LangchainQaAdapter(
        api_key=settings.openai_api_key,
        model=settings.openai_model,
    )
    context_builder = MarketContextBuilderService()
    usecase = AnalyzeQuestionUseCase(stock_data_port, question_analyzer_port, context_builder)
    return await usecase.execute(request)
