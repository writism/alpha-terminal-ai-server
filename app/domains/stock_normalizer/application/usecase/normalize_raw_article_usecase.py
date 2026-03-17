from app.domains.stock_normalizer.application.request.normalize_raw_article_request import NormalizeRawArticleRequest
from app.domains.stock_normalizer.application.response.normalize_raw_article_response import NormalizeRawArticleResponse
from app.domains.stock_normalizer.application.usecase.normalized_article_repository_port import NormalizedArticleRepositoryPort
from app.domains.stock_normalizer.domain.entity.raw_article import RawArticle
from app.domains.stock_normalizer.domain.service.article_normalizer_service import ArticleNormalizerService


class NormalizeRawArticleUseCase:
    def __init__(self, repository: NormalizedArticleRepositoryPort):
        self._repository = repository
        self._normalizer = ArticleNormalizerService()

    async def execute(self, request: NormalizeRawArticleRequest) -> NormalizeRawArticleResponse:
        raw = RawArticle(
            id=request.id,
            source_type=request.source_type,
            source_name=request.source_name,
            title=request.title,
            body_text=request.body_text,
            published_at=request.published_at,
            symbol=request.symbol,
            lang=request.lang,
        )

        article = self._normalizer.normalize(raw)
        saved = await self._repository.save(article)

        return NormalizeRawArticleResponse(
            id=saved.id,
            raw_article_id=saved.raw_article_id,
            stock_symbol=saved.stock_symbol,
            source_type=saved.source_type,
            source_name=saved.source_name,
            title=saved.title,
            body=saved.body,
            category=saved.category.value,
            published_at=saved.published_at,
            lang=saved.lang,
            content_quality=saved.content_quality.value,
            normalized_at=saved.normalized_at,
            normalizer_version=saved.normalizer_version,
        )
