from abc import ABC, abstractmethod


class QuestionAnalyzerPort(ABC):
    @abstractmethod
    async def analyze(self, context: str, question: str) -> str: ...
