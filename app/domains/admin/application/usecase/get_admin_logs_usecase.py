from sqlalchemy.orm import Session

from app.domains.pipeline.infrastructure.orm.analysis_log_orm import AnalysisLogORM
from app.domains.admin.application.response.admin_logs_response import AdminLogItem, AdminLogsResponse


class GetAdminLogsUseCase:

    def __init__(self, db: Session):
        self._db = db

    def execute(self, limit: int = 50) -> AdminLogsResponse:
        total = self._db.query(AnalysisLogORM).count()
        rows = (
            self._db.query(AnalysisLogORM)
            .order_by(AnalysisLogORM.analyzed_at.desc())
            .limit(limit)
            .all()
        )
        logs = [
            AdminLogItem(
                id=row.id,
                symbol=row.symbol,
                name=row.name,
                analyzed_at=row.analyzed_at,
                sentiment=row.sentiment,
                sentiment_score=row.sentiment_score,
                source_type=row.source_type,
                account_id=row.account_id,
            )
            for row in rows
        ]
        return AdminLogsResponse(logs=logs, total=total)
