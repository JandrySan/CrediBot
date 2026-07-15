import uuid
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.database.session import SessionLocal
from app.models.conversation import Conversation
from app.models.customer import Customer
from app.models.message import Message
from main import app


def _create_conversation(status: str = "ACTIVE", response_mode: str = "AUDIO") -> int:
    db = SessionLocal()
    try:
        unique_phone = f"+5939{uuid.uuid4().int % 100000000:08d}"
        customer = Customer(phone_number=f"whatsapp:{unique_phone}", full_name="Cliente Asesor")
        db.add(customer)
        db.commit()
        db.refresh(customer)

        conversation = Conversation(
            customer_id=customer.id,
            current_state=status,
            status=status,
            response_mode=response_mode,
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)

        return conversation.id
    finally:
        db.close()


def test_take_conversation_resets_audio_mode_and_notifies_customer():
    conversation_id = _create_conversation(status="ACTIVE", response_mode="AUDIO")

    with (
        patch(
            "app.services.dashboard.conversation_service.TwilioWhatsAppService.send_message",
            return_value={"success": True, "sid": "SM123"},
        ) as sender,
        TestClient(app) as client,
    ):
        response = client.post(f"/api/dashboard/conversations/{conversation_id}/take")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["status"] == "HANDOFF"
    assert payload["customer_notified"] is True
    assert sender.called

    db = SessionLocal()
    try:
        conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
        assert conversation is not None
        assert conversation.response_mode == "TEXT"
    finally:
        db.close()


def test_advisor_reply_is_not_saved_when_twilio_fails():
    conversation_id = _create_conversation(status="HANDOFF", response_mode="AUDIO")

    with (
        patch(
            "app.services.dashboard.conversation_service.TwilioWhatsAppService.send_message",
            return_value={"success": False, "message": "sandbox no unido"},
        ),
        TestClient(app) as client,
    ):
        response = client.post(
            f"/api/dashboard/conversations/{conversation_id}/reply",
            data={"message": "Hola, soy tu asesor."},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is False
    assert payload["message_saved"] is False
    assert payload["whatsapp_sent"] is False

    db = SessionLocal()
    try:
        saved = (
            db.query(Message)
            .filter(
                Message.conversation_id == conversation_id,
                Message.direction == "OUTBOUND",
            )
            .all()
        )
        assert saved == []
    finally:
        db.close()


def test_advisor_reply_is_saved_after_twilio_success():
    conversation_id = _create_conversation(status="HANDOFF", response_mode="AUDIO")

    with (
        patch(
            "app.services.dashboard.conversation_service.TwilioWhatsAppService.send_message",
            return_value={"success": True, "sid": "SM124"},
        ),
        TestClient(app) as client,
    ):
        response = client.post(
            f"/api/dashboard/conversations/{conversation_id}/reply",
            data={"message": "Hola, soy tu asesor."},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["message_saved"] is True
    assert payload["whatsapp_sent"] is True

    db = SessionLocal()
    try:
        saved = (
            db.query(Message)
            .filter(
                Message.conversation_id == conversation_id,
                Message.direction == "OUTBOUND",
            )
            .all()
        )
        assert len(saved) == 1
        assert saved[0].content == "Hola, soy tu asesor."
    finally:
        db.close()
