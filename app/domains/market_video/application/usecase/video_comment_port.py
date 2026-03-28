from abc import ABC, abstractmethod
from typing import List

from app.domains.market_video.domain.entity.video_comment import VideoComment


class VideoCommentPort(ABC):
    @abstractmethod
    def fetch_comments(self, video_id: str, order: str, max_count: int) -> List[VideoComment]:
        """
        :param video_id: YouTube 영상 ID
        :param order: 'time'(최신순) | 'relevance'(인기순)
        :param max_count: 최대 수집 개수
        :return: 댓글 목록 (댓글 비활성화 또는 유효하지 않은 ID이면 빈 리스트)
        """
        pass
