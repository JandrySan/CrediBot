from urllib.parse import urlparse

from app.config.settings import Settings


def validate_runtime_configuration(settings: Settings) -> None:
    """Fail at startup when an enabled integration is incomplete."""
    errors: list[str] = []

    try:
        _ = settings.database_url
    except ValueError as exc:
        errors.append(str(exc))

    if settings.DASHBOARD_AUTH_ENABLED:
        if not settings.DASHBOARD_ADMIN_PASSWORD.strip():
            errors.append("DASHBOARD_ADMIN_PASSWORD es obligatoria con autenticacion activa.")
        if len(settings.DASHBOARD_JWT_SECRET.strip()) < 32:
            errors.append("DASHBOARD_JWT_SECRET debe tener al menos 32 caracteres.")

    if settings.TWILIO_ENABLED:
        if not settings.TWILIO_ACCOUNT_SID.startswith("AC"):
            errors.append("TWILIO_ACCOUNT_SID debe ser un Account SID valido.")
        if not settings.TWILIO_AUTH_TOKEN.strip():
            errors.append("TWILIO_AUTH_TOKEN es obligatorio con Twilio activo.")
        if not settings.TWILIO_WHATSAPP_FROM.strip():
            errors.append("TWILIO_WHATSAPP_FROM es obligatorio con Twilio activo.")
        if settings.TWILIO_VALIDATE_SIGNATURE:
            parsed = urlparse(settings.TWILIO_WEBHOOK_URL)
            if parsed.scheme != "https" or not parsed.netloc:
                errors.append(
                    "TWILIO_WEBHOOK_URL debe ser una URL HTTPS publica para validar firmas."
                )

    if not settings.GROQ_API_KEY.strip():
        errors.append("GROQ_API_KEY es obligatoria para el flujo conversacional.")

    if errors:
        details = "\n- ".join(errors)
        raise RuntimeError(f"Configuracion de entorno invalida:\n- {details}")
