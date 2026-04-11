from dataclasses import dataclass, field
from typing import List


@dataclass
class UserProfile:
    """사용자 투자 성향 프로필 — AI 맞춤 분석에 사용되는 컨텍스트.

    투자 추천 용도가 아니며, AI 분석 관점 개인화에만 활용한다.
    """
    account_id: int
    investment_style: str          # "단기", "중장기", "장기"
    risk_tolerance: str            # "낮음", "중간", "높음"
    preferred_sectors: List[str]   # ["IT", "바이오", "금융"]
    analysis_preference: str       # "뉴스중심", "공시중심", "혼합"
    watchlist_symbols: List[str]   # ["060250", "234340"]
    keywords_of_interest: List[str] = field(default_factory=list)  # ["AI반도체", "2차전지"]
