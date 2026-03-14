from app.domains.post.application.request.create_post_request import CreatePostRequest
from app.domains.post.application.response.create_post_response import CreatePostResponse
from app.domains.post.application.usecase.post_repository_port import PostRepositoryPort
from app.domains.post.domain.entity.post import Post


class CreatePostUseCase:
    def __init__(self, post_repository: PostRepositoryPort):
        self._post_repository = post_repository

    def execute(self, request: CreatePostRequest) -> CreatePostResponse:
        post = Post(
            title=request.title,
            content=request.content,
            author=request.author or "익명",
        )
        saved = self._post_repository.save(post)
        return CreatePostResponse(
            id=saved.id,
            title=saved.title,
            content=saved.content,
            author=saved.author,
            created_at=saved.created_at,
        )
