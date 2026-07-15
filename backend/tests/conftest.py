import os
from pathlib import Path

TEST_DATABASE = Path(__file__).resolve().parents[1] / "work" / "pytest.db"
TEST_DATABASE.parent.mkdir(exist_ok=True)

# Configure isolation before importing any application module that builds an engine.
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DATABASE.as_posix()}"
os.environ["RUN_DB_MIGRATIONS"] = "false"
os.environ["AUTO_CREATE_DB_SCHEMA"] = "true"
os.environ["DASHBOARD_AUTH_ENABLED"] = "false"
os.environ["TWILIO_ENABLED"] = "false"
os.environ["TWILIO_VALIDATE_SIGNATURE"] = "false"
os.environ["AUDIO_STT_ENABLED"] = "false"
os.environ["GROQ_API_KEY"] = "test-groq-key"

from app.database.init_db import init_db  # noqa: E402
from app.database.session import engine  # noqa: E402


def pytest_sessionstart(session):
    _ = session
    if TEST_DATABASE.exists():
        engine.dispose()
        TEST_DATABASE.unlink()
    init_db()


def pytest_sessionfinish(session, exitstatus):
    _ = (session, exitstatus)
    engine.dispose()
    if TEST_DATABASE.exists():
        TEST_DATABASE.unlink()
