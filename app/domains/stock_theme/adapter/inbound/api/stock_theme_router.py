from typing import Optional

from fastapi import APIRouter, Cookie, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.domains.auth.adapter.outbound.in_memory.redis_session_adapter import RedisSessionAdapter
from app.domains.stock_theme.adapter.outbound.persistence.stock_theme_repository_impl import (
    StockThemeRepositoryImpl,
)
from app.domains.stock_theme.application.response.recommendation_response import RecommendationResponse
from app.domains.stock_theme.application.response.stock_theme_response import (
    StockThemeListResponse,
    StockThemeResponse,
)
from app.domains.stock_theme.application.usecase.get_stock_themes_usecase import GetStockThemesUseCase
from app.domains.stock_theme.application.usecase.recommend_stocks_usecase import RecommendStocksUseCase
from app.domains.stock_theme.application.usecase.seed_stock_themes_usecase import SeedStockThemesUseCase
from app.domains.stock_theme.adapter.inbound.deps import get_recommendation_reason_generation_service
from app.domains.stock_theme.domain.service.recommendation_reason_generation_service import (
    RecommendationReasonGenerationService,
)
from app.domains.youtube.adapter.outbound.external.kiwi_noun_extractor import KiwiNounExtractor
from app.domains.youtube.adapter.outbound.persistence.youtube_comment_repository_impl import (
    YouTubeCommentRepositoryImpl,
)
from app.domains.youtube.application.usecase.extract_nouns_usecase import ExtractNounsUseCase
from app.infrastructure.cache.redis_client import redis_client
from app.infrastructure.database.session import get_db

router = APIRouter(prefix="/stock-theme", tags=["stock-theme"])

_session_adapter = RedisSessionAdapter(redis_client)


@router.get("", response_model=StockThemeListResponse)
async def get_stock_themes(
    theme: Optional[str] = Query(default=None, description="테마 키워드로 필터링"),
    db: Session = Depends(get_db),
):
    repository = StockThemeRepositoryImpl(db)
    usecase = GetStockThemesUseCase(repository)
    return usecase.execute(theme=theme)


class RecommendRequest(BaseModel):
    keywords: dict[str, int]


@router.get("/recommend", response_model=RecommendationResponse)
async def recommend_stocks_from_keywords(
    top_n: int = Query(
        default=30,
        ge=1,
        le=200,
        description="댓글에서 쓸 상위 명사 개수(빈도 딕셔너리 크기)",
    ),
    user_token: Optional[str] = Cookie(default=None),
    db: Session = Depends(get_db),
    reason_service: RecommendationReasonGenerationService = Depends(get_recommendation_reason_generation_service),
):
    """저장된 YouTube 댓글에서 명사 빈도를 구해 테마 매칭 추천을 반환한다. `user_token` 쿠키 필요."""
    if not user_token:
        raise HTTPException(status_code=401, detail="인증이 필요합니다.")
    if _session_adapter.find_by_token(user_token) is None:
        raise HTTPException(status_code=401, detail="세션이 만료되었거나 유효하지 않습니다.")

    comment_repo = YouTubeCommentRepositoryImpl(db)
    noun_extractor = KiwiNounExtractor()
    noun_usecase = ExtractNounsUseCase(repository=comment_repo, noun_extractor=noun_extractor)
    noun_result = noun_usecase.execute(top_n=top_n)
    keywords = {item.noun: item.count for item in noun_result.nouns}

    repository = StockThemeRepositoryImpl(db)
    recommend = RecommendStocksUseCase(repository, reason_service)
    return recommend.execute(keywords)


@router.post("/recommend", response_model=RecommendationResponse)
async def recommend_stocks(
    request: RecommendRequest,
    db: Session = Depends(get_db),
    reason_service: RecommendationReasonGenerationService = Depends(get_recommendation_reason_generation_service),
):
    repository = StockThemeRepositoryImpl(db)
    usecase = RecommendStocksUseCase(repository, reason_service)
    return usecase.execute(request.keywords)


@router.post("/seed", response_model=dict)
async def seed_stock_themes(db: Session = Depends(get_db)):
    repository = StockThemeRepositoryImpl(db)
    usecase = SeedStockThemesUseCase(repository)
    count = usecase.execute()
    return {"message": f"{count}개 종목-테마 매핑이 등록되었습니다."}
