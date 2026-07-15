import pytest

from app.config.runtime import validate_runtime_configuration
from app.config.settings import Settings


def test_minimal_local_configuration_is_valid():
    configuration = Settings(
        _env_file=None,
        DATABASE_URL="sqlite:///./test.db",
        DASHBOARD_AUTH_ENABLED=False,
        TWILIO_ENABLED=False,
        AUDIO_STT_ENABLED=False,
        GROQ_API_KEY="test-groq-key",
    )

    validate_runtime_configuration(configuration)


def test_exposed_integrations_fail_fast_when_secrets_are_missing():
    configuration = Settings(
        _env_file=None,
        DATABASE_URL="sqlite:///./test.db",
        DASHBOARD_AUTH_ENABLED=True,
        DASHBOARD_ADMIN_PASSWORD="",
        DASHBOARD_JWT_SECRET="short",
        TWILIO_ENABLED=True,
        TWILIO_ACCOUNT_SID="",
        TWILIO_AUTH_TOKEN="",
        TWILIO_WHATSAPP_FROM="",
        TWILIO_WEBHOOK_URL="http://localhost/webhook/whatsapp",
        TWILIO_VALIDATE_SIGNATURE=True,
        AUDIO_STT_ENABLED=False,
        GROQ_API_KEY="test-groq-key",
    )

    with pytest.raises(RuntimeError) as error:
        validate_runtime_configuration(configuration)

    message = str(error.value)
    assert "DASHBOARD_ADMIN_PASSWORD" in message
    assert "DASHBOARD_JWT_SECRET" in message
    assert "TWILIO_ACCOUNT_SID" in message
    assert "TWILIO_WEBHOOK_URL" in message
