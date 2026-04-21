"""RunPipelineUseCase 실행 결과 DTO.

기존 `dict` 반환을 대체하여 호출측의 타입 추론을 강화한다.
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from app.domains.pipeline.application.response.analysis_log_response import AnalysisLogResponse
from app.domains.pipeline.application.response.stock_summary_response import StockSummaryResponse


class ProcessedItem(BaseModel):
    symbol: str
    skipped: bool
    reason: str | None = None
    # 확장 필드를 허용 (기존 로직이 임의 키를 추가하는 경우 대비)
    extra: dict[str, Any] = Field(default_factory=dict)


class RunPipelineResponse(BaseModel):
    """BL-BE-86: POST /pipeline/run 의 API 응답 DTO.

    유즈케이스 반환 타입(`RunPipelineResult`)과 API 응답 계약을 명시적으로 분리한다.
    """
    message: str
    processed: list[dict[str, Any]]


class RunPipelineResult(BaseModel):
    message: str
    processed: list[dict[str, Any]] = Field(default_factory=list)
    summaries: list[StockSummaryResponse] = Field(default_factory=list)
    report_summaries: list[StockSummaryResponse] = Field(default_factory=list)
    logs: list[AnalysisLogResponse] = Field(default_factory=list)
