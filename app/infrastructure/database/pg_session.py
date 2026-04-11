"""BL-BE-54: PostgreSQL 세션 및 연결 풀 — 비정형 데이터(JSONB) 저장용.

기존 MySQL(session.py)은 정형 데이터용으로 유지하고,
이 모듈은 뉴스 원문·공시 본문·리포트 등 비정형 데이터 저장에 사용한다.
"""
import logging
from urllib.parse import quote_plus

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from app.infrastructure.config.settings import get_settings

logger = logging.getLogger(__name__)


def _build_pg_url() -> str:
    s = get_settings()
    return (
        f"postgresql+psycopg2://{s.pg_user}:{quote_plus(s.pg_password)}"
        f"@{s.pg_host}:{s.pg_port}/{s.pg_database}"
    )


def _build_pg_engine():
    s = get_settings()
    return create_engine(
        _build_pg_url(),
        pool_size=s.pg_pool_size,
        max_overflow=s.pg_max_overflow,
        pool_pre_ping=True,
    )


pg_engine = _build_pg_engine()

PgSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=pg_engine)


class PgBase(DeclarativeBase):
    """JSONB 컬럼을 사용하는 PostgreSQL ORM 모델의 베이스 클래스."""
    pass


def get_pg_db():
    db = PgSessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_pg_health() -> bool:
    """PostgreSQL 연결 헬스 체크. 성공 시 True, 실패 시 False."""
    try:
        with pg_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("[PostgreSQL] 연결 성공")
        return True
    except Exception as e:
        logger.error(f"[PostgreSQL] 연결 실패: {e}")
        return False
