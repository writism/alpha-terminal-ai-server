from logging.config import fileConfig
from urllib.parse import quote_plus

from sqlalchemy import engine_from_config, pool
from alembic import context

from app.infrastructure.config.settings import get_settings
from app.infrastructure.database.pg_session import PgBase

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = PgBase.metadata


def get_url() -> str:
    s = get_settings()
    return (
        f"postgresql+psycopg2://{s.pg_user}:{quote_plus(s.pg_password)}"
        f"@{s.pg_host}:{s.pg_port}/{s.pg_database}"
    )


def run_migrations_offline() -> None:
    context.configure(
        url=get_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = get_url()
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
