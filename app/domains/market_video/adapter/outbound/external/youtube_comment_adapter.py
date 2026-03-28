from datetime import datetime, timezone
from typing import List

import httpx

from app.domains.market_video.application.usecase.video_comment_port import VideoCommentPort
from app.domains.market_video.domain.entity.video_comment import VideoComment
from app.infrastructure.config.settings import get_settings

_COMMENT_THREADS_URL = "https://www.googleapis.com/youtube/v3/commentThreads"
_MAX_RESULTS_PER_PAGE = 100  # YouTube API 허용 최대


class YoutubeCommentAdapter(VideoCommentPort):

    def fetch_comments(self, video_id: str, order: str, max_count: int) -> List[VideoComment]:
        api_key = get_settings().youtube_api_key
        comments: List[VideoComment] = []
        page_token: str | None = None

        while len(comments) < max_count:
            batch_size = min(_MAX_RESULTS_PER_PAGE, max_count - len(comments))
            params = {
                "part": "snippet",
                "videoId": video_id,
                "order": order,
                "maxResults": batch_size,
                "key": api_key,
            }
            if page_token:
                params["pageToken"] = page_token

            try:
                response = httpx.get(_COMMENT_THREADS_URL, params=params, timeout=10.0)
                # 댓글 비활성화(403) 또는 유효하지 않은 영상(404) → 빈 리스트
                if response.status_code in (403, 404):
                    return []
                response.raise_for_status()
            except httpx.HTTPStatusError:
                return []

            data = response.json()
            for item in data.get("items", []):
                comment = self._parse_item(item, video_id)
                if comment:
                    comments.append(comment)

            page_token = data.get("nextPageToken")
            if not page_token:
                break

        return comments

    @staticmethod
    def _parse_item(item: dict, video_id: str) -> VideoComment | None:
        try:
            snippet = item["snippet"]["topLevelComment"]["snippet"]
            content = snippet.get("textDisplay", "").strip()
            if not content:
                return None

            published_at_str = snippet.get("publishedAt", "")
            try:
                published_at = datetime.fromisoformat(published_at_str.replace("Z", "+00:00"))
            except ValueError:
                published_at = datetime.now(timezone.utc)

            return VideoComment(
                comment_id=item["snippet"]["topLevelComment"]["id"],
                video_id=video_id,
                author=snippet.get("authorDisplayName", ""),
                content=content,
                published_at=published_at,
                like_count=int(snippet.get("likeCount", 0)),
            )
        except (KeyError, ValueError):
            return None
