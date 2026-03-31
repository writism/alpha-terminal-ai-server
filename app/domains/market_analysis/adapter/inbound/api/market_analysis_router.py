from typing import Optional

from fastapi import APIRouter, Cookie, Depends, HTTPException
from sqlalchemy.orm import Session

from app.domains.auth.adapter.outbound.in_memory.redis_session_adapter import RedisSessionAdapter
from app.domains.market_analysis.adapter.outbound.external.langchain_qa_adapter import LangChainQAAdapter
from app.domains.market_analysis.adapter.outbound.persistence.market_data_repository_impl import (
    MarketDataRepositoryImpl,
)
from app.domains.market_analysis.application.request.analysis_request import AnalysisQueryRequest
from app.domains.market_analysis.application.response.analysis_response import AnalysisAnswerResponse
from app.domains.market_analysis.application.usecase.analyze_market_query_usecase import (
    AnalyzeMarketQueryUseCase,
)
from app.infrastructure.cache.redis_client import redis_client
from app.infrastructure.config.settings import get_settings
from app.infrastructure.database.session import get_db

router = APIRouter(prefix="/market-analysis", tags=["market-analysis"])

_session_adapter = RedisSessionAdapter(redis_client)


def _resolve_account_id(
    account_id_cookie: Optional[str],
    user_token: Optional[str],
) -> Optional[int]:
    if account_id_cookie:
        try:
            return int(account_id_cookie)
        except ValueError:
            pass
    if user_token:
        session = _session_adapter.find_by_token(user_token)
        if session:
            try:
                return int(session.user_id)
            except ValueError:
                pass
    return None


@router.post("/ask", response_model=AnalysisAnswerResponse)
async def ask_market_analysis(
    request: AnalysisQueryRequest,
    db: Session = Depends(get_db),
    account_id: Optional[str] = Cookie(default=None),
    user_token: Optional[str] = Cookie(default=None),
):
    """관심종목 기반 LangChain Q&A. `user_token` 또는 `account_id` 쿠키 필요."""
    aid = _resolve_account_id(account_id, user_token)
    if aid is None:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")

    settings = get_settings()
    repository = MarketDataRepositoryImpl(db)
    qa = LangChainQAAdapter(api_key=settings.openai_api_key, model=settings.openai_model)
    usecase = AnalyzeMarketQueryUseCase(repository, qa)
    answer = usecase.execute(account_id=aid, question=request.question)
    return AnalysisAnswerResponse(answer=answer.answer, in_scope=answer.in_scope)
