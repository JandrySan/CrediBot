import uuid

from fastapi.testclient import TestClient

from app.database.session import SessionLocal
from app.models.conversation import Conversation
from app.models.credit_application import CreditApplication
from app.models.customer import Customer
from app.repositories.conversation_repository import ConversationRepository
from main import app


def _create_handoff_conversation() -> tuple[int, int]:
    db = SessionLocal()
    try:
        unique_phone = f"+5939{uuid.uuid4().int % 100000000:08d}"
        customer = Customer(phone_number=unique_phone, full_name="Cliente Test")
        db.add(customer)
        db.commit()
        db.refresh(customer)

        application = CreditApplication(customer_id=customer.id)
        db.add(application)
        db.commit()

        conversation = Conversation(
            customer_id=customer.id,
            current_state="HANDOFF",
            status="HANDOFF",
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)

        return customer.id, conversation.id
    finally:
        db.close()


def test_close_handoff_conversation_and_start_new_on_next_interaction():
    customer_id, conversation_id = _create_handoff_conversation()

    with TestClient(app) as client:
        response = client.post(
            f"/api/dashboard/conversations/{conversation_id}/close",
            json={"resolution": "RESOLVED", "note": "Caso atendido"},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["status"] == "CLOSED"
    assert payload["state"] == "END"

    db = SessionLocal()
    try:
        closed_conversation = (
            db.query(Conversation).filter(Conversation.id == conversation_id).first()
        )
        assert closed_conversation is not None
        assert closed_conversation.status == "CLOSED"

        latest_application = (
            db.query(CreditApplication)
            .filter(CreditApplication.customer_id == customer_id)
            .order_by(CreditApplication.id.desc())
            .first()
        )
        assert latest_application is not None
        assert latest_application.result is not None

        repo = ConversationRepository(db)
        new_conversation = repo.get_or_create_active(customer_id=customer_id)
        assert new_conversation.id != conversation_id
        assert new_conversation.status == "ACTIVE"
        assert new_conversation.current_state == "START"
    finally:
        db.close()
