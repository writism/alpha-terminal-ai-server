from app.domains.llm.application.usecase.text_generation_port import TextGenerationPort
from app.infrastructure.config.settings import get_settings
from app.infrastructure.llm.openai_responses_client import OpenAIResponsesTextClient


def get_text_generation_port() -> TextGenerationPort:
    """BL-BE-50: Settings 기반 TextGenerationPort 구현체를 반환한다."""
    settings = get_settings()
    return OpenAIResponsesTextClient(
        api_key=settings.openai_api_key,
        model=settings.openai_responses_model,
    )


def get_recommendation_reason_text_generation_port() -> TextGenerationPort:
    """BL-BE-51: 추천 이유 생성용 Responses 클라이언트 (기본 모델 gpt-5-mini)."""
    settings = get_settings()
    return OpenAIResponsesTextClient(
        api_key=settings.openai_api_key,
        model=settings.openai_recommendation_reason_model,
    )
