from abc import ABC, abstractmethod
from typing import List, Tuple

from app.domains.news_search.domain.entity.news_article import NewsArticle


class NewsSearchPort(ABC):
    @abstractmethod
    def search(self, keyword: str, page: int, page_size: int) -> Tuple[List[NewsArticle], int]:
        pass
