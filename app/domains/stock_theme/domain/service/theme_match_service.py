from dataclasses import dataclass, field

from app.domains.stock_theme.domain.entity.stock_theme import StockTheme


@dataclass
class ThemeMatchResult:
    name: str
    code: str
    matched_keywords: list[str] = field(default_factory=list)
    relevance_score: float = 0.0


class ThemeMatchService:
    """추출된 키워드와 종목 테마를 매칭하여 관련성 점수를 산출하는 Domain Service."""

    def match(
        self,
        keyword_frequencies: dict[str, int],
        stock_themes: list[StockTheme],
    ) -> list[ThemeMatchResult]:
        if not keyword_frequencies or not stock_themes:
            return []

        total_freq = sum(keyword_frequencies.values())
        if total_freq == 0:
            return []

        results: list[ThemeMatchResult] = []

        for stock in stock_themes:
            matched: list[str] = []
            score = 0.0

            for theme in stock.themes:
                if theme in keyword_frequencies:
                    matched.append(theme)
                    score += keyword_frequencies[theme] / total_freq

            if matched:
                results.append(ThemeMatchResult(
                    name=stock.name,
                    code=stock.code,
                    matched_keywords=matched,
                    relevance_score=round(score, 4),
                ))

        results.sort(key=lambda r: r.relevance_score, reverse=True)
        return results
