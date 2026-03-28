from datetime import datetime, timedelta, timezone

import httpx

from app.domains.youtube.application.usecase.youtube_comment_port import YouTubeCommentPort
from app.domains.youtube.application.usecase.youtube_search_port import YouTubeSearchPort
from app.domains.youtube.domain.entity.youtube_comment import YouTubeComment
from app.domains.youtube.domain.entity.youtube_video import YouTubeVideo

YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
YOUTUBE_VIDEOS_URL = "https://www.googleapis.com/youtube/v3/videos"
YOUTUBE_COMMENT_THREADS_URL = "https://www.googleapis.com/youtube/v3/commentThreads"

# 사전 정의된 뉴스 채널
CURATED_CHANNEL_IDS = [
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


class YouTubeApiAdapter(YouTubeSearchPort, YouTubeCommentPort):
    def __init__(self, api_key: str):
        self._api_key = api_key

    async def search_stock_videos(
        self, page_token: str | None = None, max_results: int = 9,
    ) -> tuple[list[YouTubeVideo], str | None, str | None, int]:
        params: dict = {
            "part": "snippet",
            "q": "주식 종목 분석",
            "type": "video",
            "maxResults": max_results,
            "order": "date",
            "relevanceLanguage": "ko",
            "key": self._api_key,
        }
        if page_token:
            params["pageToken"] = page_token

        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(YOUTUBE_SEARCH_URL, params=params)
            resp.raise_for_status()
            data = resp.json()

        items = data.get("items", [])
        videos = [
            YouTubeVideo(
                video_id=item["id"]["videoId"],
                title=item["snippet"]["title"],
                thumbnail_url=item["snippet"]["thumbnails"]["high"]["url"],
                channel_name=item["snippet"]["channelTitle"],
                published_at=item["snippet"]["publishedAt"],
                video_url=f"https://www.youtube.com/watch?v={item['id']['videoId']}",
            )
            for item in items
            if item.get("id", {}).get("videoId")
        ]

        next_token = data.get("nextPageToken")
        prev_token = data.get("prevPageToken")
        total = data.get("pageInfo", {}).get("totalResults", 0)

        return videos, next_token, prev_token, total

    async def search_channel_videos(
        self,
        channel_id: str,
        query: str,
        published_after: datetime,
        max_results: int = 10,
    ) -> list[YouTubeVideo]:
        """특정 채널에서 query 기반 영상을 검색한다."""
        params: dict = {
            "part": "snippet",
            "channelId": channel_id,
            "q": query,
            "type": "video",
            "maxResults": max_results,
            "order": "date",
            "publishedAfter": published_after.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "key": self._api_key,
        }

        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(YOUTUBE_SEARCH_URL, params=params)
            resp.raise_for_status()
            data = resp.json()

        items = data.get("items", [])
        video_ids = [
            item["id"]["videoId"]
            for item in items
            if item.get("id", {}).get("videoId")
        ]
        if not video_ids:
            return []

        # 조회수를 가져오기 위해 videos API 호출
        view_counts = await self._fetch_view_counts(video_ids)

        videos = []
        for item in items:
            vid = item.get("id", {}).get("videoId")
            if not vid:
                continue
            videos.append(
                YouTubeVideo(
                    video_id=vid,
                    title=item["snippet"]["title"],
                    thumbnail_url=item["snippet"]["thumbnails"]["high"]["url"],
                    channel_name=item["snippet"]["channelTitle"],
                    published_at=item["snippet"]["publishedAt"],
                    video_url=f"https://www.youtube.com/watch?v={vid}",
                    view_count=view_counts.get(vid, 0),
                )
            )
        return videos

    async def collect_from_channels(
        self,
        keywords: list[str],
        days: int = 3,
        max_per_channel: int = 5,
    ) -> list[YouTubeVideo]:
        """사전 정의된 채널에서 키워드 기반 영상을 수집한다."""
        if not keywords:
            return []

        published_after = datetime.now(timezone.utc) - timedelta(days=days)
        query = " | ".join(keywords)
        all_videos: list[YouTubeVideo] = []

        for channel_id in CURATED_CHANNEL_IDS:
            try:
                videos = await self.search_channel_videos(
                    channel_id=channel_id,
                    query=query,
                    published_after=published_after,
                    max_results=max_per_channel,
                )
                all_videos.extend(videos)
            except Exception:
                continue

        # 키워드 필터링: 제목에 키워드 포함 비율
        filtered = self._filter_by_keywords(all_videos, keywords)

        # 게시일 기준 정렬 후 상위 10개
        filtered.sort(key=lambda v: v.published_at, reverse=True)
        return filtered[:10]

    @staticmethod
    def _filter_by_keywords(
        videos: list[YouTubeVideo],
        keywords: list[str],
        min_ratio: float = 0.1,
    ) -> list[YouTubeVideo]:
        """제목에 키워드 포함 비율이 min_ratio 이상인 영상만 선택한다."""
        if not keywords:
            return videos
        result = []
        for v in videos:
            title_lower = v.title.lower()
            matched = sum(1 for kw in keywords if kw.lower() in title_lower)
            ratio = matched / len(keywords)
            if ratio >= min_ratio:
                result.append(v)
        return result

    async def fetch_comments(
        self,
        video_id: str,
        max_results: int = 100,
        order: str = "relevance",
    ) -> list[YouTubeComment]:
        """commentThreads API로 영상 댓글을 조회한다."""
        comments: list[YouTubeComment] = []
        page_token: str | None = None
        remaining = max_results

        while remaining > 0:
            page_size = min(remaining, 100)  # API 최대 100
            params: dict = {
                "part": "snippet",
                "videoId": video_id,
                "maxResults": page_size,
                "order": order,
                "textFormat": "plainText",
                "key": self._api_key,
            }
            if page_token:
                params["pageToken"] = page_token

            try:
                async with httpx.AsyncClient(timeout=10) as client:
                    resp = await client.get(YOUTUBE_COMMENT_THREADS_URL, params=params)
                    if resp.status_code == 403:
                        # 댓글 비활성화된 영상
                        return []
                    resp.raise_for_status()
                    data = resp.json()
            except httpx.HTTPStatusError:
                return comments

            for item in data.get("items", []):
                snippet = item.get("snippet", {}).get("topLevelComment", {}).get("snippet", {})
                text = snippet.get("textDisplay", "").strip()
                if not text:
                    continue
                comments.append(
                    YouTubeComment(
                        comment_id=item["id"],
                        video_id=video_id,
                        author_name=snippet.get("authorDisplayName", ""),
                        text=text,
                        published_at=snippet.get("publishedAt", ""),
                        like_count=int(snippet.get("likeCount", 0)),
                    )
                )

            page_token = data.get("nextPageToken")
            remaining -= page_size
            if not page_token:
                break

        return comments

    async def _fetch_view_counts(self, video_ids: list[str]) -> dict[str, int]:
        """videos API로 조회수를 가져온다."""
        params = {
            "part": "statistics",
            "id": ",".join(video_ids),
            "key": self._api_key,
        }
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(YOUTUBE_VIDEOS_URL, params=params)
                resp.raise_for_status()
                data = resp.json()
            return {
                item["id"]: int(item.get("statistics", {}).get("viewCount", 0))
                for item in data.get("items", [])
            }
        except Exception:
            return {}
