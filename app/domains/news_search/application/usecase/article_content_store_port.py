from abc import ABC, abstractmethod
from typing import Any, Optional, TypedDict


class ArticleRawData(TypedDict, total=False):
    """기사 본문 저장소에 기록되는 JSONB raw_data 의 알려진 키.

    total=False 로 선언하여 호출처별로 부분 필드를 허용하되, 타입 체커가 알려진 키의
    타입을 검증하도록 한다. 알려지지 않은 키가 필요하면 상위에서 cast 를 사용한다.
    """

    title: str
    link: str
    snippet: str
    source: str
    published_at: str
    content: str
    keyword: str
    page: int


class ArticleContentStorePort(ABC):
    @abstractmethod
    def store(self, article_id: int, account_id: int, raw_data: "ArticleRawData | dict[str, Any]") -> None:
        pass

    @abstractmethod
    def get_content(self, article_id: int) -> Optional[str]:
        """저장된 기사 본문(raw_data.content) 반환. 없으면 None."""
        pass
