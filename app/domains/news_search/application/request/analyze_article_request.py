from pydantic import BaseModel


class AnalyzeArticleRequest(BaseModel):
    article_id: int
