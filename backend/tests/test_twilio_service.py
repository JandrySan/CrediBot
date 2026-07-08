import unittest
from types import SimpleNamespace
from unittest.mock import patch

from app.services.whatsapp import twilio_service


class TwilioServiceTests(unittest.TestCase):
    def test_send_message_uses_legacy_whatsapp_number_and_normalizes_recipient(self):
        fake_settings = SimpleNamespace(
            TWILIO_ENABLED=True,
            TWILIO_ACCOUNT_SID="sid",
            TWILIO_AUTH_TOKEN="token",
            TWILIO_WHATSAPP_NUMBER="+14155238886",
            TWILIO_WEBHOOK_URL="",
        )

        with patch.object(twilio_service, "settings", fake_settings):
            service = twilio_service.TwilioWhatsAppService()
            service.client = unittest.mock.Mock()
            service.client.messages.create.return_value.sid = "SM123"

            result = service.send_message(to="3001234567", body="Hola")

            self.assertTrue(result["success"])
            self.assertEqual(result["sid"], "SM123")
            self.assertEqual(
                service.client.messages.create.call_args.kwargs["from_"],
                "+14155238886",
            )
            self.assertEqual(
                service.client.messages.create.call_args.kwargs["to"],
                "+3001234567",
            )


if __name__ == "__main__":
    unittest.main()
