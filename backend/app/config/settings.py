from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "CrediBot"
    DEBUG: bool = True
    AI_ONLY_MODE: bool = False
    BACKEND_CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"
    DATABASE_URL: str = ""

    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "credibot"
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "12345678"

    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_WHATSAPP_FROM: str = ""
    TWILIO_WHATSAPP_NUMBER: str = ""
    TWILIO_WEBHOOK_URL: str = ""
    TWILIO_ENABLED: bool = False

    GROQ_API_KEY: str = ""

    AUDIO_STT_ENABLED: bool = True
    AUDIO_STT_PROVIDER: str = "groq"
    AUDIO_STT_MODEL: str = "base"
    AUDIO_STT_LANGUAGE: str = "es"
    AUDIO_STT_DEVICE: str = "cpu"
    AUDIO_STT_COMPUTE_TYPE: str = "int8"
    AUDIO_STT_GROQ_MODEL: str = "whisper-large-v3-turbo"
    AUDIO_STT_REQUEST_TIMEOUT_SECONDS: int = 20

    AUDIO_REPLY_ENABLED: bool = False
    AUDIO_REPLY_LANGUAGE: str = "es"
    AUDIO_REPLY_PUBLIC_BASE_URL: str = ""

    CONVERSATION_SESSION_TIMEOUT_MINUTES: int = 60
    CONVERSATION_CLEANUP_BATCH_SIZE: int = 100

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
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
        if self.DATABASE_URL:
            return self.DATABASE_URL

        return (
            f"postgresql+psycopg2://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    @property
    def cors_origins(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.BACKEND_CORS_ORIGINS.split(",")
            if origin.strip()
        ]


settings = Settings()
