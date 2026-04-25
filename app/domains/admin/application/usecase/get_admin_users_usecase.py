from sqlalchemy.orm import Session

from app.domains.account.infrastructure.orm.account_orm import AccountORM
from app.domains.admin.application.response.admin_users_response import AdminUserItem, AdminUsersResponse


class GetAdminUsersUseCase:

    def __init__(self, db: Session):
        self._db = db

    def execute(self, page: int = 1, size: int = 20) -> AdminUsersResponse:
        total = self._db.query(AccountORM).count()
        rows = (
            self._db.query(AccountORM)
            .order_by(AccountORM.created_at.desc())
            .offset((page - 1) * size)
            .limit(size)
            .all()
        )
        users = [
            AdminUserItem(
                id=row.id,
                nickname=row.nickname,
                email=row.email,
                role=row.role or "NORMAL",
                created_at=row.created_at,
            )
            for row in rows
        ]
        return AdminUsersResponse(users=users, total=total)
