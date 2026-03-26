from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.domains.card_share.adapter.outbound.persistence.card_share_repository_impl import (
    CardShareRepositoryImpl,
)
from app.domains.card_share.application.request.add_comment_request import AddCommentRequest
from app.domains.card_share.application.request.share_card_request import ShareCardRequest
from app.domains.card_share.application.response.shared_card_response import (
    CardCommentListResponse,
    CardCommentResponse,
    LikeToggleResponse,
    SharedCardListResponse,
    SharedCardResponse,
)
from app.domains.card_share.domain.entity.card_comment import CardComment
from app.domains.card_share.domain.entity.shared_card import SharedCard
from app.infrastructure.database.session import get_db
from app.infrastructure.cache.redis_client import redis_client
from app.domains.auth.adapter.outbound.in_memory.redis_session_adapter import RedisSessionAdapter

router = APIRouter(prefix="/card-share", tags=["card-share"])

_session_adapter = RedisSessionAdapter(redis_client)


def _get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _get_like_identity(request: Request, account_id: int | None) -> str:
    """좋아요 중복 방지용 식별자.
    - 로그인 사용자: account:{id}  → 같은 WiFi 내 다른 사용자와 충돌 없음
    - 익명 사용자 : guest_id 쿠키 → 없으면 IP fallback
    """
    if account_id:
        return f"account:{account_id}"
    return request.cookies.get("guest_id") or _get_client_ip(request)


def _get_current_account_id(request: Request, db: Session) -> tuple[int | None, str | None]:
    """(account_id, nickname) 반환. 비로그인이면 (None, None)."""
    user_token = request.cookies.get("user_token")
    if not user_token:
        return None, None
    session = _session_adapter.find_by_token(user_token)
    if not session:
        return None, None
    try:
        account_id = int(session.user_id)
    except (ValueError, TypeError):
        return None, None
    nickname = request.cookies.get("nickname")
    return account_id, nickname


def _to_response(card: SharedCard, user_has_liked: bool = False) -> SharedCardResponse:
    return SharedCardResponse(
        id=card.id,
        symbol=card.symbol,
        name=card.name,
        summary=card.summary,
        tags=card.tags or [],
        sentiment=card.sentiment,
        sentiment_score=card.sentiment_score,
        confidence=card.confidence,
        source_type=card.source_type,
        url=card.url,
        analyzed_at=card.analyzed_at,
        sharer_account_id=card.sharer_account_id,
        sharer_nickname=card.sharer_nickname or "익명",
        like_count=card.like_count,
        comment_count=card.comment_count,
        created_at=card.created_at,
        user_has_liked=user_has_liked,
    )


# ── Shared Cards ──────────────────────────────────────────────────────────────

@router.post("", response_model=SharedCardResponse)
async def share_card(
    body: ShareCardRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    account_id, nickname = _get_current_account_id(request, db)
    if not account_id:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")

    repo = CardShareRepositoryImpl(db)
    card = SharedCard(
        symbol=body.symbol,
        name=body.name,
        summary=body.summary,
        tags=body.tags,
        sentiment=body.sentiment,
        sentiment_score=body.sentiment_score,
        confidence=body.confidence,
        source_type=body.source_type,
        url=body.url,
        analyzed_at=body.analyzed_at,
        sharer_account_id=account_id,
        sharer_nickname=nickname or "익명",
    )
    saved = repo.save(card)
    return _to_response(saved)


@router.get("", response_model=SharedCardListResponse)
async def list_shared_cards(
    request: Request,
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    repo = CardShareRepositoryImpl(db)
    cards, total = repo.find_all(limit=limit, offset=offset)
    account_id, _ = _get_current_account_id(request, db)
    identity = _get_like_identity(request, account_id)
    liked_ids = repo.find_liked_card_ids([c.id for c in cards], identity, account_id)
    return SharedCardListResponse(
        cards=[_to_response(c, c.id in liked_ids) for c in cards],
        total=total,
    )


@router.get("/{card_id}", response_model=SharedCardResponse)
async def get_shared_card(card_id: int, request: Request, db: Session = Depends(get_db)):
    repo = CardShareRepositoryImpl(db)
    card = repo.find_by_id(card_id)
    if not card:
        raise HTTPException(status_code=404, detail="카드를 찾을 수 없습니다.")
    account_id, _ = _get_current_account_id(request, db)
    identity = _get_like_identity(request, account_id)
    liked_ids = repo.find_liked_card_ids([card_id], identity, account_id)
    return _to_response(card, card_id in liked_ids)


@router.delete("/{card_id}")
async def delete_shared_card(
    card_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    account_id, _ = _get_current_account_id(request, db)
    if not account_id:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")

    repo = CardShareRepositoryImpl(db)
    card = repo.find_by_id(card_id)
    if not card:
        raise HTTPException(status_code=404, detail="카드를 찾을 수 없습니다.")
    if card.sharer_account_id != account_id:
        raise HTTPException(status_code=403, detail="본인이 공유한 카드만 삭제할 수 있습니다.")

    repo.delete(card_id)
    return {"message": "삭제되었습니다."}


# ── Likes ─────────────────────────────────────────────────────────────────────

@router.post("/{card_id}/likes", response_model=LikeToggleResponse)
async def toggle_like(
    card_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    repo = CardShareRepositoryImpl(db)
    card = repo.find_by_id(card_id)
    if not card:
        raise HTTPException(status_code=404, detail="카드를 찾을 수 없습니다.")

    account_id, _ = _get_current_account_id(request, db)
    identity = _get_like_identity(request, account_id)

    existing = repo.find_like(card_id, identity, account_id)
    if existing:
        repo.remove_like(card_id, identity, account_id)
        like_count = repo.get_like_count(card_id)
        return LikeToggleResponse(liked=False, like_count=like_count)
    else:
        repo.add_like(card_id, identity, account_id)
        like_count = repo.get_like_count(card_id)
        return LikeToggleResponse(liked=True, like_count=like_count)


# ── Comments ──────────────────────────────────────────────────────────────────

@router.get("/{card_id}/comments", response_model=CardCommentListResponse)
async def list_comments(card_id: int, db: Session = Depends(get_db)):
    repo = CardShareRepositoryImpl(db)
    if not repo.find_by_id(card_id):
        raise HTTPException(status_code=404, detail="카드를 찾을 수 없습니다.")
    comments = repo.find_comments(card_id)
    return CardCommentListResponse(
        comments=[
            CardCommentResponse(
                id=c.id,
                shared_card_id=c.shared_card_id,
                content=c.content,
                author_nickname=c.author_nickname or "익명",
                created_at=c.created_at,
            )
            for c in comments
        ]
    )


@router.post("/{card_id}/comments", response_model=CardCommentResponse)
async def add_comment(
    card_id: int,
    body: AddCommentRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    repo = CardShareRepositoryImpl(db)
    if not repo.find_by_id(card_id):
        raise HTTPException(status_code=404, detail="카드를 찾을 수 없습니다.")

    account_id, _ = _get_current_account_id(request, db)
    client_ip = _get_client_ip(request)

    comment = CardComment(
        shared_card_id=card_id,
        content=body.content,
        author_nickname=body.author_nickname,
        author_account_id=account_id,
        author_ip=client_ip,
    )
    saved = repo.add_comment(comment)
    return CardCommentResponse(
        id=saved.id,
        shared_card_id=saved.shared_card_id,
        content=saved.content,
        author_nickname=saved.author_nickname or "익명",
        created_at=saved.created_at,
    )
