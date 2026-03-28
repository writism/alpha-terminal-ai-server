from abc import ABC, abstractmethod
from typing import List

from app.domains.market_video.domain.entity.market_video import MarketVideo


class YoutubeChannelVideoPort(ABC):
    @abstractmethod
    def fetch_recent(self, channel_ids: List[str], days_back: int) -> List[MarketVideo]:
        """지정된 채널들의 최근 days_back일 이내 영상을 반환한다."""
        pass
