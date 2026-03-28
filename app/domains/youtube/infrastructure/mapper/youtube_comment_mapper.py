from app.domains.youtube.domain.entity.youtube_comment import YouTubeComment
from app.domains.youtube.infrastructure.orm.youtube_comment_orm import YouTubeCommentORM


class YouTubeCommentMapper:
    @staticmethod
    def to_entity(orm: YouTubeCommentORM) -> YouTubeComment:
        return YouTubeComment(
            comment_id=orm.comment_id,
            video_id=orm.video_id,
            author_name=orm.author_name,
            text=orm.text,
            published_at=orm.published_at,
            like_count=orm.like_count,
        )

    @staticmethod
    def to_orm(entity: YouTubeComment) -> YouTubeCommentORM:
        return YouTubeCommentORM(
            comment_id=entity.comment_id,
            video_id=entity.video_id,
            author_name=entity.author_name,
            text=entity.text,
            published_at=entity.published_at,
            like_count=entity.like_count,
        )
