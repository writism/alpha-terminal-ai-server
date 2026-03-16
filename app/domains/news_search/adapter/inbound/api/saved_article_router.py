from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.domains.news_search.adapter.outbound.external.article_content_adapter import ArticleContentAdapter
from app.domains.news_search.adapter.outbound.persistence.saved_article_repository_impl import SavedArticleRepositoryImpl
from app.domains.news_search.application.request.save_article_request import SaveArticleRequest
from app.domains.news_search.application.response.save_article_response import SaveArticleResponse
from app.domains.news_search.application.usecase.save_article_usecase import SaveArticleUseCase
from app.infrastructure.database.session import get_db

router = APIRouter(prefix="/news", tags=["news"])


@router.post("/articles", response_model=SaveArticleResponse, status_code=201)
async def save_article(request: SaveArticleRequest, db: Session = Depends(get_db)):
    repository = SavedArticleRepositoryImpl(db)
    content_fetcher = ArticleContentAdapter()
    usecase = SaveArticleUseCase(repository, content_fetcher)
    return usecase.execute(request)
