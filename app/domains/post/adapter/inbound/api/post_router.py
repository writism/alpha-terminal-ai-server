from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.domains.post.adapter.outbound.persistence.post_repository_impl import PostRepositoryImpl
from app.domains.post.application.request.create_post_request import CreatePostRequest
from app.domains.post.application.response.create_post_response import CreatePostResponse
from app.domains.post.application.usecase.create_post_usecase import CreatePostUseCase
from app.infrastructure.database.session import get_db

router = APIRouter(prefix="/posts", tags=["posts"])


@router.post("", response_model=CreatePostResponse, status_code=201)
async def create_post(request: CreatePostRequest, db: Session = Depends(get_db)):
    repository = PostRepositoryImpl(db)
    usecase = CreatePostUseCase(repository)
    return usecase.execute(request)
