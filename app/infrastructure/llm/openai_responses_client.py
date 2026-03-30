from openai import OpenAI

from app.domains.llm.application.usecase.text_generation_port import TextGenerationPort

# BL-BE-50 Success Criteria: gpt-5-mini 또는 gpt-4.1-mini
_ALLOWED_RESPONSES_MODELS = frozenset({"gpt-4.1-mini", "gpt-5-mini"})


class OpenAIResponsesTextClient(TextGenerationPort):
    """OpenAI Responses API(`client.responses.create`) 기반 텍스트 생성 클라이언트."""

    def __init__(self, api_key: str, model: str = "gpt-4.1-mini") -> None:
        if model not in _ALLOWED_RESPONSES_MODELS:
            raise ValueError(
                f"openai_responses_model must be one of {sorted(_ALLOWED_RESPONSES_MODELS)}, got {model!r}"
            )
        self._model = model
        self._client: OpenAI | None = OpenAI(api_key=api_key) if api_key else None

    def generate(self, prompt: str) -> str:
        if not prompt or not prompt.strip():
            raise ValueError("prompt must be a non-empty string")
        if self._client is None:
            raise RuntimeError("OPENAI_API_KEY is not configured")

        response = self._client.responses.create(
            model=self._model,
            input=prompt.strip(),
        )
        text = response.output_text
        return text.strip() if text else ""
