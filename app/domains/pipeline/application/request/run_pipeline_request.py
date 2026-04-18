from enum import Enum

from pydantic import BaseModel, Field


class ArticleMode(str, Enum):
    LATEST_1 = "latest_1"   # 최신 1건
    LATEST_3 = "latest_3"   # 최신 3건 (기본값)
    LATEST_5 = "latest_5"   # 최신 5건
    LAST_24H = "last_24h"   # 24시간 내 전체


class RunPipelineRequest(BaseModel):
    symbols: list[str] = Field(default_factory=list)
    article_mode: ArticleMode = Field(default=ArticleMode.LATEST_3, description="기사 선택 모드")
