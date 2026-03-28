from app.domains.youtube.domain.entity.youtube_video import YouTubeVideo
from app.domains.youtube.infrastructure.orm.youtube_video_orm import YouTubeVideoORM


class YouTubeVideoMapper:
    @staticmethod
    def to_entity(orm: YouTubeVideoORM) -> YouTubeVideo:
        return YouTubeVideo(
            id=orm.id,
            video_id=orm.video_id,
            title=orm.title,
            thumbnail_url=orm.thumbnail_url,
            channel_name=orm.channel_name,
            published_at=orm.published_at,
            video_url=orm.video_url,
            view_count=orm.view_count or 0,
            created_at=orm.created_at,
            updated_at=orm.updated_at,
        )

    @staticmethod
    def to_orm(entity: YouTubeVideo) -> YouTubeVideoORM:
        return YouTubeVideoORM(
            id=entity.id,
            video_id=entity.video_id,
            title=entity.title,
            thumbnail_url=entity.thumbnail_url,
            channel_name=entity.channel_name,
            published_at=entity.published_at,
            video_url=entity.video_url,
            view_count=entity.view_count,
        )
