from dataclasses import dataclass


@dataclass
class AnalysisQuery:
    question: str
    account_id: int
