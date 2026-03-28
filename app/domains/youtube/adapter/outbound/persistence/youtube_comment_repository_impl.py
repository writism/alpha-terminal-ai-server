from sqlalchemy.orm import Session

from app.domains.youtube.application.usecase.youtube_comment_repository_port import YouTubeCommentRepositoryPort
from app.domains.youtube.domain.entity.youtube_comment import YouTubeComment
from app.domains.youtube.infrastructure.mapper.youtube_comment_mapper import YouTubeCommentMapper
from app.domains.youtube.infrastructure.orm.youtube_comment_orm import YouTubeCommentORM


class YouTubeCommentRepositoryImpl(YouTubeCommentRepositoryPort):
    def __init__(self, db: Session):
        self._db = db

    def upsert(self, comment: YouTubeComment) -> YouTubeComment:
        existing = (
            self._db.query(YouTubeCommentORM)
            .filter(YouTubeCommentORM.comment_id == comment.comment_id)
            .first()
        )
        if existing:
            existing.text = comment.text
            existing.like_count = comment.like_count
            self._db.commit()
            return YouTubeCommentMapper.to_entity(existing)

        orm = YouTubeCommentMapper.to_orm(comment)
        self._db.add(orm)
        self._db.commit()
        return YouTubeCommentMapper.to_entity(orm)

    def find_by_video_id(self, video_id: str) -> list[YouTubeComment]:
        rows = (
            self._db.query(YouTubeCommentORM)
            .filter(YouTubeCommentORM.video_id == video_id)
            .order_by(YouTubeCommentORM.like_count.desc())
            .all()
        )
        return [YouTubeCommentMapper.to_entity(r) for r in rows]

    def find_all(self) -> list[YouTubeComment]:
        rows = (
            self._db.query(YouTubeCommentORM)
            .order_by(YouTubeCommentORM.like_count.desc())
            .all()
        )
        return [YouTubeCommentMapper.to_entity(r) for r in rows]
