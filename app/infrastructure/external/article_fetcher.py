from html.parser import HTMLParser

import httpx


class _TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self._texts = []
        self._skip = False

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "noscript"):
            self._skip = True

    def handle_endtag(self, tag):
        if tag in ("script", "style", "noscript"):
            self._skip = False

    def handle_data(self, data):
        if not self._skip:
            text = data.strip()
            if text:
                self._texts.append(text)

    def get_text(self) -> str:
        return " ".join(self._texts)


class ArticleFetcher:
    async def fetch(self, url: str) -> str:
        try:
            async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
                response = await client.get(
                    url, headers={"User-Agent": "Mozilla/5.0"}
                )
                response.raise_for_status()
                parser = _TextExtractor()
                parser.feed(response.text)
                return parser.get_text()[:10000]
        except Exception:
            return ""
