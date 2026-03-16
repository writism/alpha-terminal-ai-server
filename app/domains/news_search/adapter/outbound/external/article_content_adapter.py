import re

import httpx

from app.domains.news_search.application.usecase.article_content_port import ArticleContentPort


class ArticleContentAdapter(ArticleContentPort):
    def fetch_content(self, url: str) -> str:
        headers = {
            "User-Agent": "AlphaDesk/1.0 (news-archiver)"
        }
        response = httpx.get(url, headers=headers, timeout=10.0, follow_redirects=True)
        response.raise_for_status()

        html = response.text
        text = re.sub(r"<script[^>]*>[\s\S]*?</script>", "", html)
        text = re.sub(r"<style[^>]*>[\s\S]*?</style>", "", text)
        text = re.sub(r"<[^>]+>", "", text)
        text = re.sub(r"\s+", " ", text).strip()

        return text
