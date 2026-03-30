from typing import Optional

from pydantic import BaseModel


class StockThemeResponse(BaseModel):
    id: Optional[int] = None
    name: str
    code: str
    themes: list[str]


class StockThemeListResponse(BaseModel):
    items: list[StockThemeResponse]
    total: int
