from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.domains.account.infrastructure.orm.account_orm import AccountORM
from app.domains.admin.application.response.admin_users_response import AdminUserItem


class UpdateUserRoleUseCase:

    def __init__(self, db: Session):
        self._db = db

    def execute(self, user_id: int, role: str) -> AdminUserItem:
        if role not in ("NORMAL", "ADMIN"):
            raise HTTPException(status_code=400, detail="role은 NORMAL 또는 ADMIN이어야 합니다.")
        row = self._db.query(AccountORM).filter(AccountORM.id == user_id).first()
        if row is None:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
        row.role = role
        self._db.commit()
        self._db.refresh(row)
        return AdminUserItem(
            id=row.id,
            nickname=row.nickname,
            email=row.email,
            role=row.role,
            created_at=row.created_at,
        )
