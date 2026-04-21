from contextlib import contextmanager
from typing import Iterator
from urllib.parse import quote_plus

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Session

from app.infrastructure.config.settings import get_settings

settings = get_settings()

DATABASE_URL = (
    f"mysql+pymysql://{settings.mysql_user}:{quote_plus(settings.mysql_password)}"
    f"@{settings.mysql_host}:{settings.mysql_port}/{settings.mysql_database}"
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def session_scope() -> Iterator[Session]:
    """FastAPI 의존성 밖(스케줄러/스레드풀 헬퍼)에서 세션을 일관되게 열고 닫기 위한 유틸.

    사용 예:
        with session_scope() as db:
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
