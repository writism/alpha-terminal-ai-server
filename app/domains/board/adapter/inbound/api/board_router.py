from typing import Optional

from fastapi import APIRouter, Cookie, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.domains.account.adapter.outbound.persistence.account_repository_impl import AccountRepositoryImpl
from app.domains.auth.adapter.outbound.in_memory.redis_session_adapter import RedisSessionAdapter
from app.domains.board.adapter.outbound.persistence.board_repository_impl import BoardRepositoryImpl
from app.domains.board.application.response.board_list_response import BoardListResponse, BoardListItemResponse
from app.domains.board.application.usecase.delete_board_usecase import DeleteBoardUseCase
from app.domains.board.application.usecase.get_board_list_usecase import GetBoardListUseCase
from app.domains.board.application.usecase.get_board_read_usecase import GetBoardReadUseCase
from app.domains.board.application.usecase.update_board_usecase import UpdateBoardUseCase
from app.domains.board.domain.entity.board import Board
from app.domains.card_share.adapter.outbound.persistence.card_share_repository_impl import (
    CardShareRepositoryImpl,
)
from app.infrastructure.cache.redis_client import redis_client
from app.infrastructure.database.session import get_db

router = APIRouter(prefix="/board", tags=["board"])

_session_adapter = RedisSessionAdapter(redis_client)


class CreateBoardRequest(BaseModel):
    title: str
    content: str
    shared_card_id: Optional[int] = None


class UpdateBoardRequest(BaseModel):
    title: str
    content: str


@router.post("", response_model=BoardListItemResponse, status_code=201)
async def create_board(
    request: CreateBoardRequest,
    account_id: Optional[str] = Cookie(default=None),
    db: Session = Depends(get_db),
):
    if not account_id:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")

    parsed_account_id = int(account_id)
    account_repository = AccountRepositoryImpl(db)
    account = account_repository.find_by_id(parsed_account_id)
    if not account:
        raise HTTPException(status_code=401, detail="존재하지 않는 계정입니다.")

    card_repo = CardShareRepositoryImpl(db)
    shared_card_id_opt: Optional[int] = None

    if request.shared_card_id is not None:
        card = card_repo.find_by_id(request.shared_card_id)
        if not card:
            raise HTTPException(status_code=400, detail="존재하지 않는 공유 카드입니다.")
        if card.sharer_account_id != parsed_account_id:
            raise HTTPException(status_code=403, detail="본인이 공유한 카드만 게시글에 연결할 수 있습니다.")
        shared_card_id_opt = request.shared_card_id
    else:
        # 일반 게시물 → 좋아요/댓글용 shared_card 자동 생성
        from datetime import datetime
        from app.domains.card_share.domain.entity.shared_card import SharedCard
        board_card = card_repo.save(SharedCard(
            symbol="BOARD",
            name=request.title[:100],
            summary=request.content[:500],
            tags=[],
            sentiment="NEUTRAL",
            sentiment_score=0.0,
            confidence=0.0,
            source_type="NEWS",
            url=None,
            analyzed_at=datetime.now(),
            sharer_account_id=parsed_account_id,
            sharer_nickname=account.nickname,
        ))
        shared_card_id_opt = board_card.id

    board_repository = BoardRepositoryImpl(db)
    saved = board_repository.save(Board(
        title=request.title,
        content=request.content,
        account_id=parsed_account_id,
        shared_card_id=shared_card_id_opt,
    ))

    return BoardListItemResponse(
        board_id=saved.id,
        title=saved.title,
        content=saved.content,
        nickname=account.nickname,
        created_at=saved.created_at,
        updated_at=saved.updated_at,
        shared_card_id=saved.shared_card_id,
    )


@router.get("/list", response_model=BoardListResponse)
async def get_board_list(
    page: int = 1,
    size: int = 10,
    account_id: Optional[str] = Cookie(default=None),
    db: Session = Depends(get_db),
):
    if not account_id:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")

    board_repository = BoardRepositoryImpl(db)
    account_repository = AccountRepositoryImpl(db)
    usecase = GetBoardListUseCase(board_repository, account_repository)
    return usecase.execute(page=page, size=size)


@router.delete("/delete/{board_id}")
async def delete_board(
    board_id: int,
    user_token: Optional[str] = Cookie(default=None),
    db: Session = Depends(get_db),
):
    if not user_token:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")

    session = _session_adapter.find_by_token(user_token)
    if not session:
        raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다.")

    account_id = int(session.user_id)
    board_repository = BoardRepositoryImpl(db)
    usecase = DeleteBoardUseCase(board_repository)

    try:
        return usecase.execute(board_id, account_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.get("/read/{board_id}", response_model=BoardListItemResponse)
async def read_board(
    board_id: int,
    user_token: Optional[str] = Cookie(default=None),
    db: Session = Depends(get_db),
):
    if not user_token:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")

    session = _session_adapter.find_by_token(user_token)
    if not session:
        raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다.")

    board_repository = BoardRepositoryImpl(db)
    account_repository = AccountRepositoryImpl(db)
    usecase = GetBoardReadUseCase(board_repository, account_repository)
    result = usecase.execute(board_id)

    if result is None:
        raise HTTPException(status_code=404, detail="게시물을 찾을 수 없습니다.")

    return result


@router.put("/{board_id}", response_model=BoardListItemResponse)
async def update_board(
    board_id: int,
    request: UpdateBoardRequest,
    account_id: Optional[str] = Cookie(default=None),
    db: Session = Depends(get_db),
):
    if not account_id:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")

    board_repository = BoardRepositoryImpl(db)
    board = board_repository.find_by_id(board_id)
    if board is None:
        raise HTTPException(status_code=404, detail="게시물을 찾을 수 없습니다.")
    if board.account_id != int(account_id):
        raise HTTPException(status_code=403, detail="수정 권한이 없습니다.")

    account_repository = AccountRepositoryImpl(db)
    usecase = UpdateBoardUseCase(board_repository, account_repository)
    result = usecase.execute(board_id, request.title, request.content)

    if result is None:
        raise HTTPException(status_code=404, detail="게시물을 찾을 수 없습니다.")

    return result


@router.get("/{board_id}", response_model=BoardListItemResponse)
async def get_board(
    board_id: int,
    account_id: Optional[str] = Cookie(default=None),
    db: Session = Depends(get_db),
):
    board_repository = BoardRepositoryImpl(db)
    board = board_repository.find_by_id(board_id)
    if not board:
        raise HTTPException(status_code=404, detail="게시물을 찾을 수 없습니다.")

    account_repository = AccountRepositoryImpl(db)
    account = account_repository.find_by_id(board.account_id)

    return BoardListItemResponse(
        board_id=board.id,
        title=board.title,
        content=board.content,
        nickname=account.nickname if account else "알 수 없음",
        created_at=board.created_at,
        updated_at=board.updated_at,
        shared_card_id=board.shared_card_id,
    )
