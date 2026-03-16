from app.domains.news_search.application.usecase.news_search_port import NewsSearchPort
from app.domains.news_search.application.response.search_news_response import (
    SearchNewsResponse,
    NewsArticleItem,
)


class SearchNewsUseCase:
    def __init__(self, news_search_port: NewsSearchPort):
        self._news_search_port = news_search_port

    def execute(self, keyword: str, page: int, page_size: int) -> SearchNewsResponse:
        articles, total_count = self._news_search_port.search(keyword, page, page_size)

        items = [
            NewsArticleItem(
                title=article.title,
                snippet=article.snippet,
                source=article.source,
                published_at=article.published_at,
                link=article.link,
            )
            for article in articles
        ]

        return SearchNewsResponse(
            items=items,
            total_count=total_count,
            page=page,
            page_size=page_size,
        )
