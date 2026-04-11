from dataclasses import dataclass, field


@dataclass
class AnalysisAnswer:
    answer: str
    in_scope: bool
    is_personalized: bool = field(default=False)
