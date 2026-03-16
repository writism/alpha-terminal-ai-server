from pydantic import BaseModel, Field


class SearchNewsRequest(BaseModel):
    keyword: str = Field(..., min_length=1)
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=10, ge=1, le=100)
