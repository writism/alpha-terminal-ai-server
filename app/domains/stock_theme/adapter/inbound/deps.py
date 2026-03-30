from app.domains.stock_theme.domain.service.recommendation_reason_generation_service import (
    RecommendationReasonGenerationService,
)
from app.infrastructure.llm.di import get_recommendation_reason_text_generation_port


def get_recommendation_reason_generation_service() -> RecommendationReasonGenerationService:
    """BL-BE-51: 추천 이유 생성 서비스 (FastAPI Depends)."""
    return RecommendationReasonGenerationService(get_recommendation_reason_text_generation_port())
