from dataclasses import dataclass


@dataclass
class AnalysisAnswer:
    answer: str
    in_scope: bool
