import pytest

from app.config.settings import Settings


def test_database_url_returns_normalized_value():
    settings = Settings(_env_file=None, DATABASE_URL=" postgresql+psycopg2://primary ")

    assert settings.database_url == "postgresql+psycopg2://primary"


def test_database_url_is_required():
    settings = Settings(_env_file=None, DATABASE_URL="")

    with pytest.raises(ValueError, match="DATABASE_URL"):
        _ = settings.database_url
