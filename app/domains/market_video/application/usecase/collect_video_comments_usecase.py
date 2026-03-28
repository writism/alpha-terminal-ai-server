from typing import List

from app.domains.market_video.application.response.video_comment_response import (
    CollectVideoCommentsResponse,
    VideoCommentGroup,
    VideoCommentItem,
)
from app.domains.market_video.application.usecase.video_comment_port import VideoCommentPort


class CollectVideoCommentsUseCase:
    DEFAULT_ORDER = "relevance"
    DEFAULT_MAX_PER_VIDEO = 20

    def __init__(self, comment_port: VideoCommentPort):
        self._comment_port = comment_port

    def execute(
        self,
        video_ids: List[str],
        order: str = DEFAULT_ORDER,
        max_per_video: int = DEFAULT_MAX_PER_VIDEO,
    ) -> CollectVideoCommentsResponse:
        """
        :param video_ids: market_videos 테이블에서 조회한 video_id 목록
        :param order: 'time'(최신순) | 'relevance'(인기순)
        :param max_per_video: 영상당 최대 수집 댓글 수
        """
        if not video_ids:
            return CollectVideoCommentsResponse(video_comments=[], total_comment_count=0)

        video_comments: List[VideoCommentGroup] = []
        seen_comment_ids: set = set()
        total = 0

        for video_id in video_ids:
            raw = self._comment_port.fetch_comments(video_id, order, max_per_video)

            deduplicated = []
            for comment in raw:
                if comment.comment_id in seen_comment_ids:
                    continue
                if not comment.content.strip():
                    continue
                seen_comment_ids.add(comment.comment_id)
                deduplicated.append(comment)

            if not deduplicated:
                continue

            video_comments.append(
                VideoCommentGroup(
                    video_id=video_id,
                    comments=[
                        VideoCommentItem(
                            comment_id=c.comment_id,
                            author=c.author,
                            content=c.content,
                            published_at=c.published_at.isoformat(),
                            like_count=c.like_count,
                        )
                        for c in deduplicated
                    ],
                )
            )
            total += len(deduplicated)

        return CollectVideoCommentsResponse(
            video_comments=video_comments,
            total_comment_count=total,
        )
