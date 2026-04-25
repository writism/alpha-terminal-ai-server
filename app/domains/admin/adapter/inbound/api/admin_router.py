from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.domains.admin.application.response.admin_dashboard_stats_response import AdminDashboardStatsResponse
from app.domains.admin.application.response.admin_logs_response import AdminLogsResponse
from app.domains.admin.application.response.admin_users_response import AdminUserItem, AdminUsersResponse
from app.domains.admin.application.usecase.get_admin_dashboard_stats_usecase import GetAdminDashboardStatsUseCase
from app.domains.admin.application.usecase.get_admin_logs_usecase import GetAdminLogsUseCase
from app.domains.admin.application.usecase.get_admin_users_usecase import GetAdminUsersUseCase
from app.domains.admin.application.usecase.update_user_role_usecase import UpdateUserRoleUseCase
from app.infrastructure.auth.require_admin import require_admin
from app.infrastructure.database.session import get_db

router = APIRouter(prefix="/admin", tags=["admin"])


class UpdateRoleRequest(BaseModel):
    role: str


@router.get("/dashboard/stats", response_model=AdminDashboardStatsResponse)
async def get_dashboard_stats(
    account_id: str = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """관리자 전용 대시보드 통계 조회. NORMAL 역할 접근 시 403."""
    return GetAdminDashboardStatsUseCase(db).execute()


@router.get("/users", response_model=AdminUsersResponse)
async def get_users(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    account_id: str = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """전체 회원 목록 (최신 가입순, 페이지네이션)."""
    return GetAdminUsersUseCase(db).execute(page=page, size=size)


@router.patch("/users/{user_id}/role", response_model=AdminUserItem)
async def update_user_role(
    user_id: int,
    body: UpdateRoleRequest,
    account_id: str = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """특정 회원의 역할을 NORMAL 또는 ADMIN으로 변경."""
    return UpdateUserRoleUseCase(db).execute(user_id=user_id, role=body.role)


@router.get("/logs", response_model=AdminLogsResponse)
async def get_logs(
    limit: int = Query(50, ge=1, le=200),
    account_id: str = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """최근 파이프라인 분석 로그 조회."""
    return GetAdminLogsUseCase(db).execute(limit=limit)
