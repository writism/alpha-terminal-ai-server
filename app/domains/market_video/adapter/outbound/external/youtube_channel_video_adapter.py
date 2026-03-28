from datetime import datetime, timedelta, timezone
from typing import List

import httpx

from app.domains.market_video.application.usecase.youtube_channel_video_port import YoutubeChannelVideoPort
from app.domains.market_video.domain.entity.market_video import MarketVideo
from app.infrastructure.config.settings import get_settings

_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
_VIDEOS_URL = "https://www.googleapis.com/youtube/v3/videos"
_MAX_RESULTS_PER_CHANNEL = 10


class YoutubeChannelVideoAdapter(YoutubeChannelVideoPort):

    def fetch_recent(self, channel_ids: List[str], days_back: int) -> List[MarketVideo]:
        api_key = get_settings().youtube_api_key
        published_after = (
            datetime.now(timezone.utc) - timedelta(days=days_back)
        ).strftime("%Y-%m-%dT%H:%M:%SZ")

        all_video_ids: List[str] = []
        for channel_id in channel_ids:
            try:
                ids = self._search_channel(channel_id, published_after, api_key)
                all_video_ids.extend(ids)
            except Exception:
                continue  # 채널 오류 시 해당 채널만 건너뜀

        if not all_video_ids:
            return []

        # 중복 제거 (순서 유지)
        unique_ids = list(dict.fromkeys(all_video_ids))
        return self._fetch_details(unique_ids, api_key)

    # ── private ──────────────────────────────────────────────────────────────

    def _search_channel(self, channel_id: str, published_after: str, api_key: str) -> List[str]:
        response = httpx.get(
            _SEARCH_URL,
            params={
                "part": "id",
                "channelId": channel_id,
                "type": "video",
                "order": "date",
                "publishedAfter": published_after,
                "maxResults": _MAX_RESULTS_PER_CHANNEL,
                "key": api_key,
            },
            timeout=10.0,
        )
        response.raise_for_status()
        return [item["id"]["videoId"] for item in response.json().get("items", [])]

    def _fetch_details(self, video_ids: List[str], api_key: str) -> List[MarketVideo]:
        results: List[MarketVideo] = []
        # YouTube API는 한 번에 최대 50개
        for i in range(0, len(video_ids), 50):
            batch = video_ids[i : i + 50]
            try:
                response = httpx.get(
                    _VIDEOS_URL,
                    params={
                        "part": "snippet,statistics",
                        "id": ",".join(batch),
                        "key": api_key,
                    },
                    timeout=10.0,
                )
                response.raise_for_status()
                for item in response.json().get("items", []):
                    video = self._parse_item(item)
                    if video:
                        results.append(video)
            except Exception:
                continue
        return results

    @staticmethod
    def _parse_item(item: dict) -> MarketVideo | None:
        try:
            snippet = item["snippet"]
            stats = item.get("statistics", {})
            thumbnails = snippet.get("thumbnails", {})
            thumbnail_url = (
                thumbnails.get("high") or thumbnails.get("medium") or thumbnails.get("default") or {}
            ).get("url", "")

            published_at_str = snippet.get("publishedAt", "")
            try:
                published_at = datetime.fromisoformat(published_at_str.replace("Z", "+00:00"))
            except ValueError:
                published_at = datetime.now(timezone.utc)

            return MarketVideo(
                video_id=item["id"],
                title=snippet.get("title", ""),
                channel_name=snippet.get("channelTitle", ""),
                published_at=published_at,
                view_count=int(stats.get("viewCount", 0)),
                thumbnail_url=thumbnail_url,
                video_url=f"https://www.youtube.com/watch?v={item['id']}",
            )
        except (KeyError, ValueError):
            return None
