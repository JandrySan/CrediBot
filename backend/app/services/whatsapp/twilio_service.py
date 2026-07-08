from twilio.rest import Client

from app.config.settings import settings


class TwilioWhatsAppService:
    def __init__(self):
        self.enabled = settings.TWILIO_ENABLED

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

        message = self.client.messages.create(
            from_=settings.TWILIO_WHATSAPP_FROM,
            to=to,
            body=body
        )

        return {
            "success": True,
            "sid": message.sid
        }