from pathlib import Path

from alembic.config import Config

from alembic import command
from app.config.settings import settings
from app.database.init_db import init_db


def prepare_database() -> None:
    if settings.RUN_DB_MIGRATIONS:
        _run_alembic_upgrade()
        return
    if settings.AUTO_CREATE_DB_SCHEMA:
        init_db()


def _run_alembic_upgrade() -> None:
    backend_root = Path(__file__).resolve().parents[2]
    config = Config(str(backend_root / "alembic.ini"))
    config.set_main_option("script_location", str(backend_root / "alembic"))
    config.set_main_option("sqlalchemy.url", settings.database_url.replace("%", "%%"))
    command.upgrade(config, "head")
