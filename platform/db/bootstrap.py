"""Create the database (if needed), run migrations, and apply curated views.

Usage:
    python -m db.bootstrap
"""
from __future__ import annotations

import pathlib

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text

from common.config import settings

ROOT = pathlib.Path(__file__).resolve().parents[1]
VIEWS = pathlib.Path(__file__).resolve().parent / "views.sql"


def _ensure_database() -> None:
    """Create the target database if it does not yet exist (connects to 'postgres')."""
    url = settings.database_url
    # strip the db name to connect to the maintenance database
    base_url, _, dbname = url.rpartition("/")
    admin_url = base_url + "/postgres"
    engine = create_engine(admin_url, isolation_level="AUTOCOMMIT", future=True)
    with engine.connect() as conn:
        exists = conn.execute(
            text("SELECT 1 FROM pg_database WHERE datname = :n"), {"n": dbname}
        ).scalar()
        if not exists:
            conn.execute(text(f'CREATE DATABASE "{dbname}"'))
    engine.dispose()


def run_migrations() -> None:
    cfg = Config(str(ROOT / "db" / "alembic.ini"))
    cfg.set_main_option("script_location", str(ROOT / "db" / "migrations"))
    cfg.set_main_option("sqlalchemy.url", settings.database_url)
    command.upgrade(cfg, "head")


def apply_views() -> None:
    engine = create_engine(settings.database_url, future=True)
    sql = VIEWS.read_text()
    with engine.begin() as conn:
        # Drop first: CREATE OR REPLACE cannot change a view's column set.
        for view in ["v_activity_current", "v_project_summary", "v_progress_trend", "v_cost_trend"]:
            conn.execute(text(f"DROP VIEW IF EXISTS {view} CASCADE"))
        for stmt in [s.strip() for s in sql.split(";") if s.strip()]:
            conn.execute(text(stmt))
    engine.dispose()


def main() -> None:
    _ensure_database()
    run_migrations()
    apply_views()
    print("Database ready: schema migrated and curated views applied.")


if __name__ == "__main__":
    main()
