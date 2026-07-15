from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DEBUG: bool = True
    AI_ONLY_MODE: bool = False
    BACKEND_CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"
    DATABASE_URL: str = ""
    RUN_DB_MIGRATIONS: bool = True
    AUTO_CREATE_DB_SCHEMA: bool = False

    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_WHATSAPP_FROM: str = ""
    TWILIO_WEBHOOK_URL: str = ""
    TWILIO_ENABLED: bool = False
    TWILIO_VALIDATE_SIGNATURE: bool = True

    DASHBOARD_AUTH_ENABLED: bool = True
    DASHBOARD_ADMIN_USERNAME: str = "admin"
    DASHBOARD_ADMIN_PASSWORD: str = ""
    DASHBOARD_ADVISOR_USERNAME: str = ""
    DASHBOARD_ADVISOR_PASSWORD: str = ""
    DASHBOARD_JWT_SECRET: str = ""
    DASHBOARD_ACCESS_TOKEN_MINUTES: int = 480

    WEBHOOK_RATE_LIMIT_PER_MINUTE: int = 120
    LOGIN_RATE_LIMIT_PER_MINUTE: int = 10

    GROQ_API_KEY: str = ""

    AUDIO_STT_ENABLED: bool = True
    AUDIO_STT_PROVIDER: str = "groq"
    AUDIO_STT_MODEL: str = "base"
    AUDIO_STT_DEVICE: str = "cpu"
    AUDIO_STT_COMPUTE_TYPE: str = "int8"
    AUDIO_STT_GROQ_MODEL: str = "whisper-large-v3-turbo"
    AUDIO_STT_REQUEST_TIMEOUT_SECONDS: int = 20

    AUDIO_REPLY_ENABLED: bool = False

    CONVERSATION_SESSION_TIMEOUT_MINUTES: int = 60
    CONVERSATION_CLEANUP_BATCH_SIZE: int = 100
    ABANDONED_CONVERSATION_RETENTION_DAYS: int = 7

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("DEBUG", mode="before")
    @classmethod
    def parse_debug(cls, value):
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"release", "production", "prod"}:
                return False
            if normalized in {"development", "dev"}:
                return True
        return value

    @property
    def database_url(self) -> str:
        database_url = self.DATABASE_URL.strip()
        if not database_url:
            raise ValueError("DATABASE_URL es obligatoria.")
        return database_url

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.BACKEND_CORS_ORIGINS.split(",") if origin.strip()]


settings = Settings()
