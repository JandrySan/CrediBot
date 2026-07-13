import uuid

from fastapi.testclient import TestClient

from app.database.session import SessionLocal
from app.models.conversation import Conversation
from app.models.credit_application import CreditApplication
from app.models.customer import Customer
from app.models.message import Message
from main import app


def _create_customer_with_multiple_applications() -> tuple[int, int]:
    db = SessionLocal()
    try:
        unique_phone = f"+5939{uuid.uuid4().int % 100000000:08d}"
        customer = Customer(phone_number=unique_phone, full_name="Cliente Duplicado Test")
        db.add(customer)
        db.commit()
        db.refresh(customer)

        first_application = CreditApplication(
            customer_id=customer.id,
            amount=1000,
            term_months=12,
            result="OBSERVADO",
        )
        second_application = CreditApplication(
            customer_id=customer.id,
            amount=2000,
            term_months=24,
            result="PREAPROBADO",
        )
        db.add(first_application)
        db.add(second_application)
        db.commit()

        conversation = Conversation(
            customer_id=customer.id,
            current_state="ACTIVE",
            status="ACTIVE",
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)

        return customer.id, conversation.id
    finally:
        db.close()


def test_get_conversations_returns_one_row_per_conversation():
    _, conversation_id = _create_customer_with_multiple_applications()

    with TestClient(app) as client:
        response = client.get("/api/dashboard/conversations")

    assert response.status_code == 200

    payload = response.json()
    matching_rows = [
        item for item in payload if item["conversation_id"] == conversation_id
    ]

    assert len(matching_rows) == 1
    assert matching_rows[0]["credit_result"] == "PREAPROBADO"
    assert matching_rows[0]["credit_amount"] == 2000.0
    assert matching_rows[0]["term_months"] == 24


def test_get_conversations_hides_closed_empty_rows_even_with_credit_result():
    db = SessionLocal()
    try:
        unique_phone = f"+5939{uuid.uuid4().int % 100000000:08d}"
        customer = Customer(phone_number=unique_phone, full_name="Cliente Cerrado Vacio")
        db.add(customer)
        db.commit()
        db.refresh(customer)

        application = CreditApplication(
            customer_id=customer.id,
            amount=2000,
            term_months=24,
            result="PREAPROBADO",
        )
        closed_empty = Conversation(
            customer_id=customer.id,
            current_state="END",
            status="CLOSED",
            result="RESUELTO_ASESOR",
        )
        db.add_all([application, closed_empty])
        db.commit()
        db.refresh(closed_empty)
        conversation_id = closed_empty.id
    finally:
        db.close()

    with TestClient(app) as client:
        response = client.get("/api/dashboard/conversations")

    assert response.status_code == 200
    assert all(
        item["conversation_id"] != conversation_id
        for item in response.json()
    )


def test_get_conversations_hides_abandoned_closed_rows_with_messages():
    db = SessionLocal()
    try:
        unique_phone = f"+5939{uuid.uuid4().int % 100000000:08d}"
        customer = Customer(phone_number=unique_phone, full_name="Cliente Expirado")
        db.add(customer)
        db.commit()
        db.refresh(customer)

        abandoned = Conversation(
            customer_id=customer.id,
            current_state="END",
            status="CLOSED",
            result="EXPIRADO",
        )
        db.add(abandoned)
        db.commit()
        db.refresh(abandoned)

        db.add(
            Message(
                conversation_id=abandoned.id,
                direction="INBOUND",
                message_type="TEXT",
                content="hola",
            )
        )
        db.commit()
        conversation_id = abandoned.id
    finally:
        db.close()

    with TestClient(app) as client:
        response = client.get("/api/dashboard/conversations")

    assert response.status_code == 200
    assert all(
        item["conversation_id"] != conversation_id
        for item in response.json()
    )


def test_get_conversations_keeps_closed_resolved_rows_with_messages():
    db = SessionLocal()
    try:
        unique_phone = f"+5939{uuid.uuid4().int % 100000000:08d}"
        customer = Customer(phone_number=unique_phone, full_name="Cliente Resuelto")
        db.add(customer)
        db.commit()
        db.refresh(customer)

        resolved = Conversation(
            customer_id=customer.id,
            current_state="END",
            status="CLOSED",
            result="RESUELTO_ASESOR",
        )
        db.add(resolved)
        db.commit()
        db.refresh(resolved)

        db.add(
            Message(
                conversation_id=resolved.id,
                direction="INBOUND",
                message_type="TEXT",
                content="necesito ayuda",
            )
        )
        db.commit()
        conversation_id = resolved.id
    finally:
        db.close()

    with TestClient(app) as client:
        response = client.get("/api/dashboard/conversations")

    assert response.status_code == 200
    assert any(
        item["conversation_id"] == conversation_id
        for item in response.json()
    )
