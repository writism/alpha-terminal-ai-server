from app.domains.youtube.application.response.youtube_comment_response import (
    YouTubeCommentListResponse,
    YouTubeCommentResponse,
)
from app.domains.youtube.application.usecase.youtube_comment_port import YouTubeCommentPort
from app.domains.youtube.application.usecase.youtube_comment_repository_port import YouTubeCommentRepositoryPort


class CollectYouTubeCommentsUseCase:
    def __init__(
        self,
        youtube_comment: YouTubeCommentPort,
        repository: YouTubeCommentRepositoryPort | None = None,
    ):
        self._youtube_comment = youtube_comment
        self._repository = repository

    async def execute(
        self,
        video_id: str,
        max_results: int = 100,
        order: str = "relevance",
    ) -> YouTubeCommentListResponse:
        comments = await self._youtube_comment.fetch_comments(
            video_id=video_id,
            max_results=max_results,
            order=order,
        )

        # 빈 텍스트 제외 + comment_id 기반 중복 제거
        seen: set[str] = set()
        unique_comments: list[YouTubeCommentResponse] = []
        for c in comments:
            if not c.text.strip():
                continue
            if c.comment_id in seen:
                continue
            seen.add(c.comment_id)

            # DB에 upsert 저장
            if self._repository:
                self._repository.upsert(c)

            unique_comments.append(
                YouTubeCommentResponse(
                    comment_id=c.comment_id,
                    video_id=c.video_id,
                    author_name=c.author_name,
                    text=c.text,
                    published_at=c.published_at,
                    like_count=c.like_count,
                )
            )

        return YouTubeCommentListResponse(
            items=unique_comments,
            video_id=video_id,
            total_collected=len(unique_comments),
        )
