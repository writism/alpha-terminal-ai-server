from app.domains.news_search.domain.entity.saved_article import SavedArticle
from app.domains.news_search.infrastructure.orm.saved_article_orm import SavedArticleORM


class SavedArticleMapper:
    @staticmethod
    def to_entity(orm: SavedArticleORM) -> SavedArticle:
        return SavedArticle(
            id=orm.id,
            title=orm.title,
            link=orm.link,
            source=orm.source,
            snippet=orm.snippet,
            content=orm.content,
            published_at=orm.published_at,
            saved_at=orm.saved_at,
        )

    @staticmethod
    def to_orm(entity: SavedArticle) -> SavedArticleORM:
        return SavedArticleORM(
            title=entity.title,
            link=entity.link,
            source=entity.source,
            snippet=entity.snippet,
            content=entity.content,
            published_at=entity.published_at,
        )
