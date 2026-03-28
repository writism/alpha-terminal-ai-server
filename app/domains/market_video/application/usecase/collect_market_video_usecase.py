from typing import List

from app.domains.market_video.application.response.collect_market_video_response import (
    CollectMarketVideoResponse,
    CollectedVideoItem,
)
from app.domains.market_video.application.usecase.market_video_repository_port import MarketVideoRepositoryPort
from app.domains.market_video.application.usecase.youtube_channel_video_port import YoutubeChannelVideoPort
from app.domains.market_video.domain.entity.market_video import MarketVideo


class CollectMarketVideoUseCase:
    CHANNEL_IDS: List[str] = [
        "UCF8AeLlUbEpKju6v1H6p8Eg",  # 한국경제TV
        "UCbMjg2EvXs_RUGW-KrdM3pw",  # SBS Biz
        "UCTHCOPwqNfZ0uiKOvFyhGwg",  # 연합뉴스TV
        "UCcQTRi69dsVYHN3exePtZ1A",  # KBS News
        "UCG9aFJTZ-lMCHAiO1KJsirg",  # MBN
        "UCsU-I-vHLiaMfV_ceaYz5rQ",  # JTBC News
        "UClErHbdZKUnD1NyIUeQWvuQ",  # 머니투데이
        "UC8Sv6O3Ux8ePVqorx8aOBMg",  # 이데일리TV
        "UCnfwIKyFYRuqZzzKBDt6JOA",  # 매일경제TV
    ]
    TOP_N = 10
    DAYS_BACK = 7

    def __init__(
        self,
        channel_video_port: YoutubeChannelVideoPort,
        repository: MarketVideoRepositoryPort,
    ):
        self._channel_port = channel_video_port
        self._repository = repository

    def execute(self, stock_names: List[str]) -> CollectMarketVideoResponse:
        """
        :param stock_names: 사용자 관심종목 이름 목록 (watchlist 기반)
        """
        if not self.CHANNEL_IDS:
            return CollectMarketVideoResponse(videos=[], saved_count=0)

        if not stock_names:
            return CollectMarketVideoResponse(videos=[], saved_count=0)

        raw_videos = self._channel_port.fetch_recent(self.CHANNEL_IDS, self.DAYS_BACK)

        filtered = [v for v in raw_videos if self._matches_watchlist(v.title, stock_names)]

        sorted_videos = sorted(filtered, key=lambda v: v.published_at, reverse=True)

        top_videos = sorted_videos[: self.TOP_N]

        if not top_videos:
            return CollectMarketVideoResponse(videos=[], saved_count=0)

        saved = self._repository.upsert_all(top_videos)

        return CollectMarketVideoResponse(
            videos=[self._to_item(v) for v in saved],
            saved_count=len(saved),
        )

    @staticmethod
    def _matches_watchlist(title: str, stock_names: List[str]) -> bool:
        """영상 제목이 사용자 관심종목 이름 중 하나라도 포함하면 True."""
        title_lower = title.lower()
        return any(name.lower() in title_lower for name in stock_names)

    @staticmethod
    def _to_item(v: MarketVideo) -> CollectedVideoItem:
        return CollectedVideoItem(
            video_id=v.video_id,
            title=v.title,
            channel_name=v.channel_name,
            published_at=v.published_at.isoformat(),
            view_count=v.view_count,
            thumbnail_url=v.thumbnail_url,
            video_url=v.video_url,
        )
