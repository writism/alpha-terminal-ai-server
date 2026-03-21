from pydantic import BaseModel, Field


class BulkAnalyzeRequest(BaseModel):
    query: str = Field(..., min_length=1)
    page_size: int = Field(default=10, ge=1, le=50)
