from abc import ABC, abstractmethod

from app.domains.market_analysis.domain.entity.analysis_answer import AnalysisAnswer


class LangChainQAPort(ABC):
    @abstractmethod
    def ask(self, question: str, context: str) -> AnalysisAnswer: ...
