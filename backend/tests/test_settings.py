from app.config.settings import Settings


def test_database_url_prefers_database_url():
    settings = Settings(
        DATABASE_URL="postgresql+psycopg2://primary",
        SUPABASE_DATABASE_URL="postgresql+psycopg2://supabase",
    )

    assert settings.database_url == "postgresql+psycopg2://primary"


def test_database_url_uses_supabase_database_url_as_fallback():
    settings = Settings(
        DATABASE_URL="",
        SUPABASE_DATABASE_URL="postgresql+psycopg2://supabase",
    )

    assert settings.database_url == "postgresql+psycopg2://supabase"
