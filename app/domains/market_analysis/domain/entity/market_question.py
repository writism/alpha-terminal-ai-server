from dataclasses import dataclass


@dataclass
class MarketQuestion:
    user_id: int
    question: str
