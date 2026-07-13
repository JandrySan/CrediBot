from twilio.base.exceptions import TwilioRestException
from twilio.rest import Client
import time

from app.config.settings import settings


class TwilioWhatsAppService:
    def __init__(self):
        self.enabled = bool(
            settings.TWILIO_ENABLED
            and settings.TWILIO_ACCOUNT_SID
            and settings.TWILIO_AUTH_TOKEN
        )
        self.client = None
        self._config_error = None

        if not self.enabled:
            return

        sid = settings.TWILIO_ACCOUNT_SID.strip()
        if sid.startswith("SK"):
            self.enabled = False
            self._config_error = (
                "TWILIO_ACCOUNT_SID parece ser una API Key (SK...). "
                "Debes usar el Account SID (empieza con AC...) desde la consola de Twilio."
            )
            return

        if not sid.startswith("AC"):
            self.enabled = False
            self._config_error = (
                "TWILIO_ACCOUNT_SID no es válido. "
                "Debe empezar con AC... (Account SID de tu consola Twilio)."
            )
            return

        self._config_error = None
        self.client = Client(sid, settings.TWILIO_AUTH_TOKEN)

    def send_message(self, to: str, body: str):
        if not self.enabled:
            return {
                "success": False,
                "message": self._config_error or (
                    "Twilio está desactivado. Configura TWILIO_ENABLED=true y las credenciales en .env"
                ),
            }

        from_number = self._normalize_phone_number(self._get_from_number())
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
            status_result = self._wait_for_send_status(message.sid, message)
            if not status_result["success"]:
                return status_result

            return {
                "success": True,
                "sid": message.sid,
                "status": status_result.get("status"),
                "from": from_number,
                "to": to_number,
            }
        except TwilioRestException as exc:
            error_code = getattr(exc, "code", None)
            if error_code == 20003:
                return {
                    "success": False,
                    "message": (
                        "Credenciales de Twilio inválidas. Verifica que TWILIO_ACCOUNT_SID "
                        "empiece con AC... y que TWILIO_AUTH_TOKEN sea el Auth Token principal "
                        "de tu cuenta (no una API Key SK...)."
                    ),
                    "error_code": error_code,
                }

            return {
                "success": False,
                "message": str(exc),
                "error_code": error_code,
            }
        except Exception as exc:  # pragma: no cover - defensive fallback
            return {
                "success": False,
                "message": str(exc)
            }

    def _wait_for_send_status(self, message_sid: str, initial_message):
        status = (getattr(initial_message, "status", "") or "").lower()
        error_code = getattr(initial_message, "error_code", None)
        error_message = getattr(initial_message, "error_message", None)

        if not status:
            return {"success": True, "sid": message_sid, "status": None}

        success_statuses = {"sent", "delivered", "read"}
        failure_statuses = {"failed", "undelivered"}
        pending_statuses = {"accepted", "scheduled", "queued", "sending"}

        for _ in range(5):
            if status in success_statuses:
                return {"success": True, "sid": message_sid, "status": status}

            if status in failure_statuses:
                return {
                    "success": False,
                    "sid": message_sid,
                    "status": status,
                    "error_code": error_code,
                    "message": self._friendly_delivery_error(error_code, error_message),
                }

            if status not in pending_statuses:
                return {"success": True, "sid": message_sid, "status": status}

            time.sleep(1)
            fetched = self.client.messages(message_sid).fetch()
            status = (getattr(fetched, "status", "") or "").lower()
            error_code = getattr(fetched, "error_code", None)
            error_message = getattr(fetched, "error_message", None)

        return {
            "success": False,
            "sid": message_sid,
            "status": status,
            "error_code": error_code,
            "message": (
                "Twilio acepto el mensaje, pero no confirmo el envio a WhatsApp. "
                "Revisa que el cliente siga unido al Sandbox y los logs de Twilio."
            ),
        }

    @staticmethod
    def _friendly_delivery_error(error_code, error_message) -> str:
        if error_code == 63015:
            return (
                "Twilio no pudo entregar el mensaje porque el numero destino no esta unido "
                "al Sandbox de WhatsApp actual, se unio a otro sandbox o su union expiro. "
                "El cliente debe enviar nuevamente el codigo join del Sandbox configurado."
            )

        return error_message or "Twilio no pudo entregar el mensaje de WhatsApp."

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

        if value.lower().startswith("whatsapp:"):
            value = value.split(":", 1)[1]

        value = value.strip()
        if value.startswith("+"):
            e164 = value
        elif value.startswith("00"):
            e164 = f"+{value[2:]}"
        else:
            e164 = f"+{value}"

        return f"whatsapp:{e164}"
