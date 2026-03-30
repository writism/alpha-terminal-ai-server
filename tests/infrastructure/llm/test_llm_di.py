from unittest.mock import MagicMock, patch

from app.domains.llm.application.usecase.text_generation_port import TextGenerationPort
from app.infrastructure.llm.di import get_text_generation_port
from app.infrastructure.llm.openai_responses_client import OpenAIResponsesTextClient


@patch("app.infrastructure.llm.openai_responses_client.OpenAI")
@patch("app.infrastructure.llm.di.get_settings")
def test_get_text_generation_port는_설정으로_OpenAIResponsesTextClient를_반환(
    mock_get_settings,
    mock_openai_cls,
):
    mock_get_settings.return_value = MagicMock(
        openai_api_key="sk-x",
        openai_responses_model="gpt-4.1-mini",
    )

    port = get_text_generation_port()

    assert isinstance(port, TextGenerationPort)
    assert isinstance(port, OpenAIResponsesTextClient)
    mock_openai_cls.assert_called_once_with(api_key="sk-x")
