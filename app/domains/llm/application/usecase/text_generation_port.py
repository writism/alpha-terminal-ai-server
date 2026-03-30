from abc import ABC, abstractmethod


class TextGenerationPort(ABC):
    """프롬프트를 받아 LLM이 생성한 텍스트를 반환한다 (BL-BE-50)."""

    @abstractmethod
    def generate(self, prompt: str) -> str:
        """동기 호출. 빈 문자열이 아닌 `prompt`를 기대한다."""
