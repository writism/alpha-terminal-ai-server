from datetime import datetime

from app.domains.stock_normalizer.application.request.normalize_disclosure_request import NormalizeDisclosureRequest
from app.domains.stock_normalizer.application.response.normalize_disclosure_response import NormalizeDisclosureResponse
from app.domains.stock_normalizer.application.usecase.normalized_disclosure_repository_port import NormalizedDisclosureRepositoryPort
from app.domains.stock_normalizer.domain.entity.normalized_disclosure import NormalizedDisclosure


class NormalizeDisclosureUseCase:
    def __init__(self, repository: NormalizedDisclosureRepositoryPort):
        self._repository = repository

    async def execute(self, request: NormalizeDisclosureRequest) -> NormalizeDisclosureResponse:
        self._validate(request)

        disclosure = NormalizedDisclosure(
            rcept_no=request.rcept_no.strip(),
            title=request.report_nm.strip(),
            content=request.content.strip(),
            disclosed_at=self._parse_date(request.rcept_dt),
            stock_code=request.stock_code.strip(),
        )

        saved = await self._repository.save(disclosure)

        return NormalizeDisclosureResponse(
            rcept_no=saved.rcept_no,
            title=saved.title,
            content=saved.content,
            disclosed_at=saved.disclosed_at,
            stock_code=saved.stock_code,
        )

    def _validate(self, request: NormalizeDisclosureRequest) -> None:
        missing = [
            field for field, value in {
                "rcept_no": request.rcept_no,
                "report_nm": request.report_nm,
                "content": request.content,
                "rcept_dt": request.rcept_dt,
                "stock_code": request.stock_code,
            }.items()
            if not value or not value.strip()
        ]
        if missing:
            raise ValueError(f"필수 필드 누락: {', '.join(missing)}")

    def _parse_date(self, rcept_dt: str) -> datetime:
        rcept_dt = rcept_dt.strip()
        if len(rcept_dt) == 8:
            return datetime.strptime(rcept_dt, "%Y%m%d")
        elif len(rcept_dt) == 14:
            return datetime.strptime(rcept_dt, "%Y%m%d%H%M%S")
        raise ValueError(f"공시일시 형식 오류: {rcept_dt} (예: '20240314' 또는 '20240314120000')")
