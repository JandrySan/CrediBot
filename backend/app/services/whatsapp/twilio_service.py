from twilio.base.exceptions import TwilioRestException
from twilio.rest import Client

from app.config.settings import settings


class TwilioWhatsAppService:
    def __init__(self):
        self.enabled = bool(
            settings.TWILIO_ENABLED
            and settings.TWILIO_ACCOUNT_SID
            and settings.TWILIO_AUTH_TOKEN
        )

        if self.enabled:
            self.client = Client(
                settings.TWILIO_ACCOUNT_SID,
                settings.TWILIO_AUTH_TOKEN
            )
        else:
            self.client = None

    def send_message(self, to: str, body: str):
        if not self.enabled:
            return {
                "success": False,
                "message": "Twilio está desactivado"
            }

        from_number = self._get_from_number()
        to_number = self._normalize_phone_number(to)

        if not from_number:
            return {
                "success": False,
                "message": "No hay un número de WhatsApp configurado en Twilio"
            }

        if not to_number:
            return {
                "success": False,
                "message": "El número de destino no es válido"
            }

        try:
            message = self.client.messages.create(
                from_=from_number,
                to=to_number,
                body=body
            )

            return {
                "success": True,
                "sid": message.sid
            }
        except TwilioRestException as exc:
            return {
                "success": False,
                "message": str(exc),
                "error_code": getattr(exc, "code", None)
            }
        except Exception as exc:  # pragma: no cover - defensive fallback
            return {
                "success": False,
                "message": str(exc)
            }

    def _get_from_number(self) -> str:
        return (
            getattr(settings, "TWILIO_WHATSAPP_FROM", None)
            or getattr(settings, "TWILIO_WHATSAPP_NUMBER", None)
            or ""
        ).strip()

    @staticmethod
    def _normalize_phone_number(phone_number: str) -> str:
        value = (phone_number or "").strip()
        if not value:
            return ""

        if value.startswith("whatsapp:"):
            value = value.split(":", 1)[1]

        if value.startswith("+"):
            return value

        if value.startswith("00"):
            return f"+{value[2:]}"

        return f"+{value}"