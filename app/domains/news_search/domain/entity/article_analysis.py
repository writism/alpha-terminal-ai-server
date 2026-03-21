from dataclasses import dataclass
from typing import List


@dataclass
class ArticleAnalysis:
    article_id: int
    keywords: List[str]
    sentiment: str        # POSITIVE | NEGATIVE | NEUTRAL
    sentiment_score: float  # -1.0 (부정) ~ 1.0 (긍정)
