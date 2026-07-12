from app.database.init_db import init_db


def pytest_sessionstart(session):
    init_db()
