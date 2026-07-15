from fastapi import HTTPException, Request, status
from twilio.request_validator import RequestValidator

from app.config.settings import settings


async def validate_twilio_signature(request: Request) -> None:
    if not settings.TWILIO_ENABLED or not settings.TWILIO_VALIDATE_SIGNATURE:
        return

    signature = request.headers.get("X-Twilio-Signature", "")
    if not signature or not settings.TWILIO_AUTH_TOKEN:
        raise _invalid_signature()

    form = await request.form()
    request_url = (settings.TWILIO_WEBHOOK_URL or str(request.url)).strip()
    validator = RequestValidator(settings.TWILIO_AUTH_TOKEN)
    if not validator.validate(request_url, dict(form), signature):
        raise _invalid_signature()


def _invalid_signature() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Firma de Twilio invalida.",
    )
