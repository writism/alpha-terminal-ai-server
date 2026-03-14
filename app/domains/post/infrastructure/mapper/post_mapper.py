from app.domains.post.domain.entity.post import Post
from app.domains.post.infrastructure.orm.post_orm import PostORM


class PostMapper:
    @staticmethod
    def to_entity(orm: PostORM) -> Post:
        return Post(
            id=orm.id,
            title=orm.title,
            content=orm.content,
            author=orm.author,
            created_at=orm.created_at,
        )

    @staticmethod
    def to_orm(entity: Post) -> PostORM:
        return PostORM(
            title=entity.title,
            content=entity.content,
            author=entity.author,
        )
