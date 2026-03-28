from datetime import datetime
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.domains.youtube.application.usecase.youtube_video_repository_port import YouTubeVideoRepositoryPort
from app.domains.youtube.domain.entity.youtube_video import YouTubeVideo
from app.domains.youtube.infrastructure.mapper.youtube_video_mapper import YouTubeVideoMapper
from app.domains.youtube.infrastructure.orm.youtube_video_orm import YouTubeVideoORM


class YouTubeVideoRepositoryImpl(YouTubeVideoRepositoryPort):
    def __init__(self, db: Session):
        self._db = db

    def find_by_video_id(self, video_id: str) -> Optional[YouTubeVideo]:
        orm = self._db.query(YouTubeVideoORM).filter(
            YouTubeVideoORM.video_id == video_id,
        ).first()
        if orm is None:
            return None
        return YouTubeVideoMapper.to_entity(orm)

    def save(self, video: YouTubeVideo) -> YouTubeVideo:
        orm = YouTubeVideoMapper.to_orm(video)
        self._db.add(orm)
        self._db.commit()
        self._db.refresh(orm)
        return YouTubeVideoMapper.to_entity(orm)

    def update(self, video: YouTubeVideo) -> YouTubeVideo:
        orm = self._db.query(YouTubeVideoORM).filter(
            YouTubeVideoORM.video_id == video.video_id,
        ).first()
        if orm is None:
            return self.save(video)
        orm.title = video.title
        orm.thumbnail_url = video.thumbnail_url
        orm.channel_name = video.channel_name
        orm.published_at = video.published_at
        orm.video_url = video.video_url
        orm.view_count = video.view_count
        orm.updated_at = datetime.now()
        self._db.commit()
        self._db.refresh(orm)
        return YouTubeVideoMapper.to_entity(orm)

    def find_all_ordered(self, limit: int = 9, offset: int = 0) -> tuple[list[YouTubeVideo], int]:
        total = self._db.query(func.count(YouTubeVideoORM.id)).scalar() or 0
        orms = (
            self._db.query(YouTubeVideoORM)
            .order_by(YouTubeVideoORM.published_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        return [YouTubeVideoMapper.to_entity(o) for o in orms], total
