from typing import List, Optional

from fastapi import APIRouter, Cookie, Depends, HTTPException
from sqlalchemy.orm import Session

from app.domains.auth.adapter.outbound.in_memory.redis_session_adapter import RedisSessionAdapter
from app.domains.watchlist.adapter.outbound.persistence.watchlist_repository_impl import WatchlistRepositoryImpl
from app.domains.watchlist.application.request.add_watchlist_request import AddWatchlistRequest
from app.domains.watchlist.infrastructure.orm.watchlist_item_orm import WatchlistItemORM
from app.domains.watchlist.application.response.watchlist_response import WatchlistItemResponse
from app.domains.watchlist.application.usecase.add_watchlist_usecase import AddWatchlistUseCase
from app.domains.watchlist.application.usecase.get_watchlist_usecase import GetWatchlistUseCase
from app.domains.watchlist.application.usecase.remove_watchlist_usecase import RemoveWatchlistUseCase
from app.infrastructure.cache.redis_client import redis_client
from app.infrastructure.database.session import get_db

router = APIRouter(prefix="/watchlist", tags=["watchlist"])

_session_adapter = RedisSessionAdapter(redis_client)


def _resolve_account_id(
    account_id_cookie: Optional[str],
    user_token: Optional[str],
) -> Optional[int]:
    """account_id 쿠키가 없거나 깨졌을 때 user_token 세션으로 복구 (카드/마켓비디오와 동일 패턴)."""
    if account_id_cookie:
        try:
            return int(account_id_cookie)
        except ValueError:
            pass
    if user_token:
        session = _session_adapter.find_by_token(user_token)
        if session:
            try:
                return int(session.user_id)
            except ValueError:
                pass
    return None


@router.post("", response_model=WatchlistItemResponse, status_code=201)
async def add_watchlist(
    request: AddWatchlistRequest,
    db: Session = Depends(get_db),
    account_id: Optional[str] = Cookie(default=None),
    user_token: Optional[str] = Cookie(default=None),
):
    aid = _resolve_account_id(account_id, user_token)
    if aid is None:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")

    repository = WatchlistRepositoryImpl(db)
    usecase = AddWatchlistUseCase(repository)
    try:
        return usecase.execute(request, account_id=aid)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.get("", response_model=List[WatchlistItemResponse])
async def get_watchlist(
    db: Session = Depends(get_db),
    account_id: Optional[str] = Cookie(default=None),
    user_token: Optional[str] = Cookie(default=None),
):
    aid = _resolve_account_id(account_id, user_token)
    if aid is None:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")

    repository = WatchlistRepositoryImpl(db)
    usecase = GetWatchlistUseCase(repository)
    return usecase.execute(account_id=aid)


@router.delete("/{item_id}", status_code=204)
async def remove_watchlist(
    item_id: int,
    db: Session = Depends(get_db),
    account_id: Optional[str] = Cookie(default=None),
    user_token: Optional[str] = Cookie(default=None),
):
    aid = _resolve_account_id(account_id, user_token)
    if aid is None:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")

    orm = db.query(WatchlistItemORM).filter(WatchlistItemORM.id == item_id).first()
    if orm is None:
        raise HTTPException(status_code=404, detail="관심종목을 찾을 수 없습니다.")
    if orm.account_id != aid:
        raise HTTPException(status_code=403, detail="삭제 권한이 없습니다.")

    repository = WatchlistRepositoryImpl(db)

    usecase = RemoveWatchlistUseCase(repository)
    try:
        usecase.execute(item_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
