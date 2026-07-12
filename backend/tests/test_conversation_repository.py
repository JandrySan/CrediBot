import unittest
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.base import Base
from app.models.conversation import Conversation
from app.repositories.conversation_repository import ConversationRepository


class ConversationRepositoryTests(unittest.TestCase):
    def test_get_or_create_active_reuses_handoff_conversation(self):
        db = MagicMock()
        handoff_conversation = SimpleNamespace(
            id=10,
            customer_id=1,
            status="HANDOFF",
            current_state="HANDOFF",
        )

        query = MagicMock()
        db.query.return_value = query
        query.filter.return_value = query
        query.order_by.return_value = query
        query.first.return_value = handoff_conversation

        repo = ConversationRepository(db)
        conversation = repo.get_or_create_active(customer_id=1)

        self.assertEqual(conversation.id, 10)
        self.assertEqual(conversation.status, "HANDOFF")
        db.add.assert_not_called()

    def test_get_or_create_active_closes_expired_session_and_creates_new_one(self):
        db = _session()
        try:
            expired = Conversation(
                customer_id=1,
                status="ACTIVE",
                current_state="ASK_AMOUNT",
                created_at=datetime.now(timezone.utc) - timedelta(minutes=30),
                updated_at=datetime.now(timezone.utc) - timedelta(minutes=30),
            )
            db.add(expired)
            db.commit()
            db.refresh(expired)

            repo = ConversationRepository(db)
            conversation = repo.get_or_create_active(customer_id=1, timeout_minutes=5)

            db.refresh(expired)
            self.assertEqual(expired.status, "CLOSED")
            self.assertEqual(expired.current_state, "END")
            self.assertEqual(expired.result, "EXPIRADO")
            self.assertNotEqual(conversation.id, expired.id)
            self.assertEqual(conversation.status, "ACTIVE")
            self.assertEqual(conversation.current_state, "START")
        finally:
            db.close()

    def test_restore_session_returns_open_session_when_not_expired(self):
        db = _session()
        try:
            active = Conversation(
                customer_id=2,
                status="ACTIVE",
                current_state="ASK_INCOME",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            db.add(active)
            db.commit()
            db.refresh(active)

            restored = ConversationRepository(db).restore_session(
                customer_id=2,
                timeout_minutes=60,
            )

            self.assertIsNotNone(restored)
            self.assertEqual(restored.id, active.id)
        finally:
            db.close()

    def test_cleanup_expired_open_sessions_closes_matching_rows(self):
        db = _session()
        try:
            old_active = Conversation(
                customer_id=3,
                status="ACTIVE",
                current_state="ASK_NAME",
                created_at=datetime.now(timezone.utc) - timedelta(minutes=90),
                updated_at=datetime.now(timezone.utc) - timedelta(minutes=90),
            )
            fresh_active = Conversation(
                customer_id=4,
                status="ACTIVE",
                current_state="ASK_NAME",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            db.add_all([old_active, fresh_active])
            db.commit()

            closed_count = ConversationRepository(db).cleanup_expired_open_sessions(
                timeout_minutes=30,
                limit=10,
            )

            db.refresh(old_active)
            db.refresh(fresh_active)
            self.assertEqual(closed_count, 1)
            self.assertEqual(old_active.status, "CLOSED")
            self.assertEqual(fresh_active.status, "ACTIVE")
        finally:
            db.close()


def _session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    testing_session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return testing_session()


if __name__ == "__main__":
    unittest.main()
