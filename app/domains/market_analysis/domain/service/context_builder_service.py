from dataclasses import dataclass, field
from typing import Optional


@dataclass
class WatchlistContext:
    symbol: str
    name: str
    themes: list[str] = field(default_factory=list)


class ContextBuilderService:
    """관심종목·테마·사용자 프로필을 LangChain 프롬프트 컨텍스트 문자열로 조합하는 Domain Service."""

    def build(self, stocks: list[WatchlistContext], user_profile: Optional[object] = None) -> str:
        lines = []

        # BL-BE-56: 사용자 프로필이 있으면 컨텍스트 상단에 추가
        if user_profile:
            lines.append("[사용자 투자 성향]")
            lines.append(f"- 투자 스타일: {user_profile.investment_style}")
            lines.append(f"- 위험 허용도: {user_profile.risk_tolerance}")
            lines.append(f"- 관심 섹터: {', '.join(user_profile.preferred_sectors)}")
            lines.append(f"- 분석 선호: {user_profile.analysis_preference}")
            if user_profile.keywords_of_interest:
                lines.append(f"- 관심 키워드: {', '.join(user_profile.keywords_of_interest)}")
            lines.append("")

        if not stocks:
            lines.append("사용자의 관심종목이 없습니다.")
            return "\n".join(lines)

        lines.append("[사용자 관심종목 및 테마]")
        for stock in stocks:
            themes_str = ", ".join(stock.themes) if stock.themes else "테마 정보 없음"
            lines.append(f"- {stock.name} ({stock.symbol}): {themes_str}")
        return "\n".join(lines)
