from unittest.mock import MagicMock, patch

import pytest

from app.infrastructure.llm.openai_responses_client import OpenAIResponsesTextClient


def test_허용되지_않은_모델이면_ValueError():
    with pytest.raises(ValueError, match="openai_responses_model"):
        OpenAIResponsesTextClient(api_key="sk-test", model="gpt-4o")


@patch("app.infrastructure.llm.openai_responses_client.OpenAI")
def test_generate는_responses_create와_output_text를_사용(mock_openai_cls):
    mock_resp = MagicMock()
    mock_resp.output_text = "  hello  "
    mock_client = MagicMock()
    mock_client.responses.create.return_value = mock_resp
    mock_openai_cls.return_value = mock_client

    client = OpenAIResponsesTextClient(api_key="sk-test", model="gpt-4.1-mini")
    out = client.generate(" prompt ")

    assert out == "hello"
    mock_client.responses.create.assert_called_once_with(
        model="gpt-4.1-mini",
        input="prompt",
    )


def test_api_키가_없으면_generate에서_RuntimeError():
    client = OpenAIResponsesTextClient(api_key="", model="gpt-4.1-mini")
    with pytest.raises(RuntimeError, match="OPENAI_API_KEY"):
        client.generate("hi")


@patch("app.infrastructure.llm.openai_responses_client.OpenAI")
def test_빈_프롬프트면_ValueError(mock_openai_cls):
    mock_openai_cls.return_value = MagicMock()
    client = OpenAIResponsesTextClient(api_key="sk-x", model="gpt-4.1-mini")
    with pytest.raises(ValueError, match="non-empty"):
        client.generate("   ")


@patch("app.infrastructure.llm.openai_responses_client.OpenAI")
def test_gpt_5_mini_모델_허용(mock_openai_cls):
    mock_openai_cls.return_value = MagicMock()
    OpenAIResponsesTextClient(api_key="sk-test", model="gpt-5-mini")
