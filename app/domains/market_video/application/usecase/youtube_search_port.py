from abc import ABC, abstractmethod
from typing import List, Optional, Tuple

from app.domains.market_video.domain.entity.youtube_video import YoutubeVideo


class YoutubeSearchPort(ABC):
    @abstractmethod
    def search(self, page_token: Optional[str], stock_name: Optional[str] = None) -> Tuple[List[YoutubeVideo], Optional[str], Optional[str], int]:
        """
        :return: (videos, next_page_token, prev_page_token, total_results)
        """
        pass
