"""
Alembic env.py — 이 프로젝트용 완성본

사용법:
  1. 프로젝트 루트에서 `alembic init alembic` 실행
  2. 생성된 alembic/env.py 를 이 파일로 덮어쓰기
     cp docs/db/env.py alembic/env.py
"""

import os
import sys
from logging.config import fileConfig
from urllib.parse import quote_plus

from alembic import context
from sqlalchemy import engine_from_config, pool

# 프로젝트 루트를 sys.path에 추가 (app 패키지 import 가능하게)
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.infrastructure.config.settings import get_settings
from app.infrastructure.database.session import Base

# ↓ ORM 모델 전체 import — autogenerate가 변경을 감지하려면 반드시 필요
# 새 도메인 ORM 추가 시 여기에도 추가할 것
from app.domains.account.infrastructure.orm.account_orm import AccountORM  # noqa: F401
from app.domains.watchlist.infrastructure.orm.watchlist_item_orm import WatchlistItemORM  # noqa: F401
from app.domains.news_search.infrastructure.orm.saved_article_orm import SavedArticleORM  # noqa: F401
from app.domains.stock_collector.infrastructure.orm.raw_article_orm import RawArticleORM  # noqa: F401
from app.domains.post.infrastructure.orm.post_orm import PostORM  # noqa: F401

# alembic.ini 로깅 설정 적용
config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# .env 기반으로 DB URL 설정 (alembic.ini의 sqlalchemy.url 대신 사용)
settings = get_settings()
DB_URL = (
    f"mysql+pymysql://{settings.mysql_user}:{quote_plus(settings.mysql_password)}"
    f"@{settings.mysql_host}:{settings.mysql_port}/{settings.mysql_database}"
)
config.set_main_option("sqlalchemy.url", DB_URL)

# autogenerate 비교 대상
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """DB 연결 없이 SQL 파일로 출력하는 모드."""
    context.configure(
        url=DB_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """실제 DB에 접속해서 마이그레이션 실행하는 모드."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
