from typing import Any, Dict

import httpx

SERP_API_URL = "https://serpapi.com/search"


class SerpClient:
    def __init__(self, api_key: str):
        self._api_key = api_key

    async def search_news(self, keyword: str, page: int, size: int) -> Dict[str, Any]:
        params = {
            "engine": "google",
            "q": keyword,
            "tbm": "nws",
            "num": size,
            "start": (page - 1) * size,
            "api_key": self._api_key,
        }
        async with httpx.AsyncClient() as client:
            response = await client.get(SERP_API_URL, params=params, timeout=10.0)
            response.raise_for_status()
            return response.json()
