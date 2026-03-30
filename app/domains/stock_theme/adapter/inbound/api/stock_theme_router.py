from typing import Optional

from fastapi import APIRouter, Cookie, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

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
from app.infrastructure.database.session import get_db

router = APIRouter(prefix="/stock-theme", tags=["stock-theme"])


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


@router.post("/recommend", response_model=RecommendationResponse)
async def recommend_stocks(
    request: RecommendRequest,
    db: Session = Depends(get_db),
):
    repository = StockThemeRepositoryImpl(db)
    usecase = RecommendStocksUseCase(repository)
    return usecase.execute(request.keywords)


@router.post("/seed", response_model=dict)
async def seed_stock_themes(db: Session = Depends(get_db)):
    repository = StockThemeRepositoryImpl(db)
    usecase = SeedStockThemesUseCase(repository)
    count = usecase.execute()
    return {"message": f"{count}개 종목-테마 매핑이 등록되었습니다."}
