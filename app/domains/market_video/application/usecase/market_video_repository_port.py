from abc import ABC, abstractmethod
from typing import List

from app.domains.market_video.domain.entity.market_video import MarketVideo


class MarketVideoRepositoryPort(ABC):
    @abstractmethod
    def upsert_all(self, videos: List[MarketVideo]) -> List[MarketVideo]:
        """videoId 기준 upsert. 성공한 영상만 반환한다."""
        pass
