from sqlalchemy.orm import Session

from app.domains.post.application.usecase.post_repository_port import PostRepositoryPort
from app.domains.post.domain.entity.post import Post
from app.domains.post.infrastructure.mapper.post_mapper import PostMapper


class PostRepositoryImpl(PostRepositoryPort):
    def __init__(self, db: Session):
        self._db = db

    def save(self, post: Post) -> Post:
        orm = PostMapper.to_orm(post)
        self._db.add(orm)
        self._db.commit()
        self._db.refresh(orm)
        return PostMapper.to_entity(orm)
