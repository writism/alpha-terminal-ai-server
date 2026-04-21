"""BL-BE-60: 기사 본문을 PostgreSQL JSONB에 저장·조회하는 어댑터."""
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.domains.news_search.application.usecase.article_content_store_port import (
    ArticleContentStorePort,
    ArticleRawData,
)
from app.domains.news_search.infrastructure.orm.saved_article_content_orm import SavedArticleContentORM


class ArticleContentStoreImpl(ArticleContentStorePort):
    def __init__(self, pg_db: Session):
        self._db = pg_db

    def store(self, article_id: int, account_id: int, raw_data: "ArticleRawData | dict[str, Any]") -> None:
        orm = SavedArticleContentORM(
            article_id=article_id,
            account_id=account_id,
            raw_data=raw_data,
        )
        self._db.add(orm)
        self._db.commit()

    def get_content(self, article_id: int) -> Optional[str]:
        orm = (
            self._db.query(SavedArticleContentORM)
            .filter(SavedArticleContentORM.article_id == article_id)
            .first()
        )
        if orm is None:
            return None
        return orm.raw_data.get("content")
