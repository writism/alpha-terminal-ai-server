from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
from urllib.parse import quote_plus

from sqlalchemy import create_engine, text


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.infrastructure.config.settings import get_settings  # noqa: E402


TARGET_REVISION = "f84b02321df9"
REQUIRED_COLUMNS = {
    "accounts": {"role", "is_watchlist_public"},
    "user_interactions": {"name", "market"},
    "analysis_logs": {"article_published_at", "source_name"},
}


@dataclass
class CheckResult:
    name: str
    passed: bool
    detail: str


def build_engine(database_name: str):
    settings = get_settings()
    database_url = (
        f"mysql+pymysql://{settings.mysql_user}:{quote_plus(settings.mysql_password)}"
        f"@{settings.mysql_host}:{settings.mysql_port}/{database_name}"
    )
    return create_engine(database_url)


def run_alembic_current(database_name: str) -> str:
    alembic_bin = REPO_ROOT / ".venv/bin/alembic"
    cmd = [str(alembic_bin), "-c", "alembic_mysql.ini", "current"]
    env = os.environ.copy()
    env["ALEMBIC_MYSQL_DATABASE"] = database_name
    completed = subprocess.run(
        cmd,
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    output = (completed.stdout + "\n" + completed.stderr).strip()
    if completed.returncode != 0:
        raise RuntimeError(output or "alembic current failed")
    return output


def fetch_version(engine) -> str | None:
    with engine.connect() as conn:
        table_exists = conn.execute(
            text("SHOW TABLES LIKE 'alembic_version'")
        ).scalar()
        if not table_exists:
            return None
        return conn.execute(text("SELECT version_num FROM alembic_version")).scalar()


def fetch_columns(engine) -> dict[str, set[str]]:
    query = text(
        """
        SELECT TABLE_NAME, COLUMN_NAME
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND (
            (TABLE_NAME = 'accounts' AND COLUMN_NAME IN ('role', 'is_watchlist_public'))
            OR
            (TABLE_NAME = 'user_interactions' AND COLUMN_NAME IN ('name', 'market'))
            OR
            (TABLE_NAME = 'analysis_logs' AND COLUMN_NAME IN ('article_published_at', 'source_name'))
          )
        """
    )
    found: dict[str, set[str]] = {}
    with engine.connect() as conn:
        for table_name, column_name in conn.execute(query):
            found.setdefault(table_name, set()).add(column_name)
    return found


def fetch_index_names(engine, table_name: str) -> set[str]:
    with engine.connect() as conn:
        rows = conn.execute(text(f"SHOW INDEX FROM {table_name}"))
        return {row[2] for row in rows}


def format_missing_columns(found: dict[str, set[str]]) -> str:
    missing: list[str] = []
    for table_name, required in REQUIRED_COLUMNS.items():
        for column_name in sorted(required - found.get(table_name, set())):
            missing.append(f"{table_name}.{column_name}")
    return ", ".join(missing)


def build_results(database_name: str) -> Iterable[CheckResult]:
    settings = get_settings()
    engine = build_engine(database_name)

    alembic_current = run_alembic_current(database_name)
    yield CheckResult(
        name="alembic current",
        passed=TARGET_REVISION in alembic_current,
        detail=alembic_current.replace("\n", " | "),
    )

    version_num = fetch_version(engine)
    yield CheckResult(
        name="alembic_version",
        passed=version_num == TARGET_REVISION,
        detail=f"version_num={version_num}",
    )

    found_columns = fetch_columns(engine)
    missing_columns = format_missing_columns(found_columns)
    yield CheckResult(
        name="remaining runtime columns",
        passed=not missing_columns,
        detail=missing_columns or "all 6 columns present",
    )

    saved_article_indexes = fetch_index_names(engine, "saved_articles")
    yield CheckResult(
        name="saved_articles follow-up index",
        passed="ix_saved_articles_account_id" in saved_article_indexes,
        detail=f"indexes={sorted(saved_article_indexes)}",
    )

    card_like_indexes = fetch_index_names(engine, "card_likes")
    yield CheckResult(
        name="card_likes follow-up unique",
        passed="uq_card_like_account" in card_like_indexes,
        detail=f"indexes={sorted(card_like_indexes)}",
    )

    host_detail = (
        f"mysql_host={settings.mysql_host}, mysql_port={settings.mysql_port}, "
        f"mysql_database={database_name}"
    )
    yield CheckResult(
        name="target database",
        passed=True,
        detail=host_detail,
    )


def main() -> int:
    settings = get_settings()
    database_name = os.getenv("ALEMBIC_MYSQL_DATABASE", settings.mysql_database)

    print("MySQL runtime migration readiness check")
    print(f"target_revision={TARGET_REVISION}")
    print(f"database={database_name}")
    print("")

    try:
        results = list(build_results(database_name))
    except Exception as exc:
        print(f"[FAIL] readiness check aborted: {exc}")
        return 1

    all_passed = True
    for result in results:
        status = "PASS" if result.passed else "FAIL"
        print(f"[{status}] {result.name}: {result.detail}")
        all_passed = all_passed and result.passed

    print("")
    if all_passed:
        print("Overall result: READY_TO_REMOVE_RUNTIME_MIGRATIONS")
        return 0

    print("Overall result: NOT_READY")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
