from typing import List, Tuple

import httpx

from app.domains.news_search.application.usecase.news_search_port import NewsSearchPort
from app.domains.news_search.domain.entity.news_article import NewsArticle
from app.infrastructure.config.settings import get_settings


class SerpNewsSearchAdapter(NewsSearchPort):
    SERP_API_URL = "https://serpapi.com/search"

    def search(self, keyword: str, page: int, page_size: int) -> Tuple[List[NewsArticle], int]:
        settings = get_settings()
        start = (page - 1) * page_size

        params = {
            "engine": "google_news",
            "q": keyword,
            "api_key": settings.serp_api_key,
            "start": start,
            "num": page_size,
        }

        response = httpx.get(self.SERP_API_URL, params=params, timeout=10.0)
        response.raise_for_status()
        data = response.json()

        news_results = data.get("news_results", [])
        total_count = data.get("search_information", {}).get("total_results", len(news_results))

        articles = [
            NewsArticle(
                title=item.get("title", ""),
                snippet=item.get("snippet", ""),
                source=item.get("source", {}).get("name", ""),
                published_at=item.get("date", None),
                link=item.get("link", None),
            )
            for item in news_results
        ]

        return articles, total_count
