from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.domains.market_analysis.application.usecase.stock_data_port import StockData


class MarketContextBuilderService:
    """DB에서 조회한 종목/테마 데이터를 LangChain 프롬프트 컨텍스트 텍스트로 변환한다."""

    def build_context(self, stocks: list["StockData"]) -> str:
        if not stocks:
            return "[등록된 종목 데이터 없음]"

        lines = ["[Alpha-Desk 추적 종목 및 테마 데이터]"]
        for stock in stocks:
            themes = ", ".join(stock.themes) if stock.themes else "테마 없음"
            lines.append(f"- {stock.name} ({stock.code}): {themes}")
        return "\n".join(lines)
