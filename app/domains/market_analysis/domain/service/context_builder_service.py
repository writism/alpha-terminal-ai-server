from dataclasses import dataclass, field


@dataclass
class WatchlistContext:
    symbol: str
    name: str
    themes: list[str] = field(default_factory=list)


class ContextBuilderService:
    """관심종목과 테마 데이터를 LangChain 프롬프트 컨텍스트 문자열로 조합하는 Domain Service."""

    def build(self, stocks: list[WatchlistContext]) -> str:
        if not stocks:
            return "사용자의 관심종목이 없습니다."

        lines = ["[사용자 관심종목 및 테마]"]
        for stock in stocks:
            themes_str = ", ".join(stock.themes) if stock.themes else "테마 정보 없음"
            lines.append(f"- {stock.name} ({stock.symbol}): {themes_str}")
        return "\n".join(lines)
