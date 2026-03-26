from app.domains.card_share.domain.entity.card_comment import CardComment
from app.domains.card_share.domain.entity.card_like import CardLike
from app.domains.card_share.domain.entity.shared_card import SharedCard
from app.domains.card_share.infrastructure.orm.card_comment_orm import CardCommentORM
from app.domains.card_share.infrastructure.orm.card_like_orm import CardLikeORM
from app.domains.card_share.infrastructure.orm.shared_card_orm import SharedCardORM


def orm_to_shared_card(orm: SharedCardORM) -> SharedCard:
    return SharedCard(
        id=orm.id,
        symbol=orm.symbol,
        name=orm.name,
        summary=orm.summary,
        tags=orm.tags or [],
        sentiment=orm.sentiment,
        sentiment_score=orm.sentiment_score,
        confidence=orm.confidence,
        source_type=orm.source_type,
        url=orm.url,
        analyzed_at=orm.analyzed_at,
        sharer_account_id=orm.sharer_account_id,
        sharer_nickname=orm.sharer_nickname,
        like_count=orm.like_count,
        comment_count=orm.comment_count,
        created_at=orm.created_at,
    )


def shared_card_to_orm(card: SharedCard) -> SharedCardORM:
    return SharedCardORM(
        symbol=card.symbol,
        name=card.name,
        summary=card.summary,
        tags=card.tags,
        sentiment=card.sentiment,
        sentiment_score=card.sentiment_score,
        confidence=card.confidence,
        source_type=card.source_type,
        url=card.url,
        analyzed_at=card.analyzed_at,
        sharer_account_id=card.sharer_account_id,
        sharer_nickname=card.sharer_nickname,
        like_count=card.like_count,
        comment_count=card.comment_count,
        created_at=card.created_at,
    )


def orm_to_card_like(orm: CardLikeORM) -> CardLike:
    return CardLike(
        id=orm.id,
        shared_card_id=orm.shared_card_id,
        liker_ip=orm.liker_ip,
        liker_account_id=orm.liker_account_id,
        created_at=orm.created_at,
    )


def orm_to_card_comment(orm: CardCommentORM) -> CardComment:
    return CardComment(
        id=orm.id,
        shared_card_id=orm.shared_card_id,
        content=orm.content,
        author_nickname=orm.author_nickname,
        author_account_id=orm.author_account_id,
        author_ip=orm.author_ip,
        created_at=orm.created_at,
    )
