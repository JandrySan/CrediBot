import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from app.services.whatsapp import twilio_service


FAKE_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "AC0000000000000000000000000000000")
FAKE_API_KEY_SID = os.getenv("TWILIO_API_KEY_SID", "SK0000000000000000000000000000000")
FAKE_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "test-auth-token")


class TwilioServiceTests(unittest.TestCase):
    def test_rejects_api_key_sid_instead_of_account_sid(self):
        fake_settings = SimpleNamespace(
            TWILIO_ENABLED=True,
            TWILIO_ACCOUNT_SID=FAKE_API_KEY_SID,
            TWILIO_AUTH_TOKEN=FAKE_AUTH_TOKEN,
            TWILIO_WHATSAPP_NUMBER="+14155238886",
            TWILIO_WEBHOOK_URL="",
        )

        with patch.object(twilio_service, "settings", fake_settings):
            service = twilio_service.TwilioWhatsAppService()
            result = service.send_message(to="3001234567", body="Hola")

            self.assertFalse(result["success"])
            self.assertIn("AC", result["message"])

    def test_send_message_uses_legacy_whatsapp_number_and_normalizes_recipient(self):
        fake_settings = SimpleNamespace(
            TWILIO_ENABLED=True,
            TWILIO_ACCOUNT_SID=FAKE_ACCOUNT_SID,
            TWILIO_AUTH_TOKEN=FAKE_AUTH_TOKEN,
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
                "whatsapp:+14155238886",
            )
            self.assertEqual(
                service.client.messages.create.call_args.kwargs["to"],
                "whatsapp:+3001234567",
            )

    def test_send_message_reports_twilio_delivery_failure_after_create(self):
        fake_settings = SimpleNamespace(
            TWILIO_ENABLED=True,
            TWILIO_ACCOUNT_SID=FAKE_ACCOUNT_SID,
            TWILIO_AUTH_TOKEN=FAKE_AUTH_TOKEN,
            TWILIO_WHATSAPP_NUMBER="+14155238886",
            TWILIO_WEBHOOK_URL="",
        )

        with patch.object(twilio_service, "settings", fake_settings), patch.object(
            twilio_service.time,
            "sleep",
        ):
            service = twilio_service.TwilioWhatsAppService()
            service.client = unittest.mock.Mock()
            created = unittest.mock.Mock()
            created.sid = "SM123"
            created.status = "queued"
            created.error_code = None
            created.error_message = None
            failed = unittest.mock.Mock()
            failed.status = "undelivered"
            failed.error_code = 63016
            failed.error_message = "User not joined to sandbox"
            service.client.messages.create.return_value = created
            service.client.messages.return_value.fetch.return_value = failed

            result = service.send_message(to="3001234567", body="Hola")

            self.assertFalse(result["success"])
            self.assertEqual(result["sid"], "SM123")
            self.assertEqual(result["status"], "undelivered")
            self.assertEqual(result["error_code"], 63016)

    def test_normalize_phone_number_accepts_existing_whatsapp_prefix_case_insensitive(self):
        normalized = twilio_service.TwilioWhatsAppService._normalize_phone_number(
            " WhatsApp:+593999999999 "
        )

        self.assertEqual(normalized, "whatsapp:+593999999999")


if __name__ == "__main__":
    unittest.main()
