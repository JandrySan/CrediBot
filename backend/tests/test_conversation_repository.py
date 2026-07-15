import unittest
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.database.base import Base
from app.models.ai_analysis import AIAnalysis
from app.models.conversation import Conversation
from app.models.conversation_state_history import ConversationStateHistory
from app.models.message import Message
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
                created_at=datetime.now(UTC) - timedelta(minutes=30),
                updated_at=datetime.now(UTC) - timedelta(minutes=30),
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
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
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
                created_at=datetime.now(UTC) - timedelta(minutes=90),
                updated_at=datetime.now(UTC) - timedelta(minutes=90),
            )
            fresh_active = Conversation(
                customer_id=4,
                status="ACTIVE",
                current_state="ASK_NAME",
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
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

    def test_purge_abandoned_closed_sessions_deletes_only_stale_abandoned_rows(self):
        db = _session()
        try:
            old_abandoned = Conversation(
                customer_id=5,
                status="CLOSED",
                current_state="END",
                result="EXPIRADO",
                created_at=datetime.now(UTC) - timedelta(days=10),
                updated_at=datetime.now(UTC) - timedelta(days=10),
            )
            fresh_abandoned = Conversation(
                customer_id=6,
                status="CLOSED",
                current_state="END",
                result="EXPIRADO",
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )
            advisor_closed = Conversation(
                customer_id=7,
                status="CLOSED",
                current_state="END",
                result="RESUELTO_ASESOR",
                created_at=datetime.now(UTC) - timedelta(days=10),
                updated_at=datetime.now(UTC) - timedelta(days=10),
            )
            db.add_all([old_abandoned, fresh_abandoned, advisor_closed])
            db.commit()
            db.refresh(old_abandoned)
            db.refresh(fresh_abandoned)
            db.refresh(advisor_closed)

            db.add_all(
                [
                    Message(
                        conversation_id=old_abandoned.id,
                        direction="INBOUND",
                        message_type="TEXT",
                        content="hola",
                    ),
                    AIAnalysis(
                        conversation_id=old_abandoned.id,
                        intent="saludo",
                        extracted_data="{}",
                        model_used="test",
                    ),
                    ConversationStateHistory(
                        conversation_id=old_abandoned.id,
                        previous_state="ASK_NAME",
                        new_state="END",
                        reason="expirada",
                    ),
                ]
            )
            db.commit()
            old_abandoned_id = old_abandoned.id
            fresh_abandoned_id = fresh_abandoned.id
            advisor_closed_id = advisor_closed.id

            deleted_count = ConversationRepository(db).purge_abandoned_closed_sessions(
                retention_days=7,
                limit=10,
            )

            self.assertEqual(deleted_count, 1)
            self.assertIsNone(db.get(Conversation, old_abandoned_id))
            self.assertIsNotNone(db.get(Conversation, fresh_abandoned_id))
            self.assertIsNotNone(db.get(Conversation, advisor_closed_id))
            self.assertEqual(db.query(Message).count(), 0)
            self.assertEqual(db.query(AIAnalysis).count(), 0)
            self.assertEqual(db.query(ConversationStateHistory).count(), 0)
        finally:
            db.close()

    def test_purge_abandoned_closed_sessions_is_disabled_when_retention_is_zero(self):
        db = _session()
        try:
            old_abandoned = Conversation(
                customer_id=8,
                status="CLOSED",
                current_state="END",
                result="EXPIRADO",
                created_at=datetime.now(UTC) - timedelta(days=10),
                updated_at=datetime.now(UTC) - timedelta(days=10),
            )
            db.add(old_abandoned)
            db.commit()
            db.refresh(old_abandoned)

            deleted_count = ConversationRepository(db).purge_abandoned_closed_sessions(
                retention_days=0,
                limit=10,
            )

            self.assertEqual(deleted_count, 0)
            self.assertIsNotNone(db.get(Conversation, old_abandoned.id))
        finally:
            db.close()

    def test_purge_empty_closed_sessions_deletes_closed_rows_without_messages(self):
        db = _session()
        try:
            closed_empty = Conversation(
                customer_id=9,
                status="CLOSED",
                current_state="END",
                result="RESUELTO_ASESOR",
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )
            active_empty = Conversation(
                customer_id=10,
                status="ACTIVE",
                current_state="START",
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )
            db.add_all([closed_empty, active_empty])
            db.commit()
            db.refresh(closed_empty)
            db.refresh(active_empty)
            closed_empty_id = closed_empty.id
            active_empty_id = active_empty.id

            deleted_count = ConversationRepository(db).purge_empty_closed_sessions(limit=10)

            self.assertEqual(deleted_count, 1)
            self.assertIsNone(db.get(Conversation, closed_empty_id))
            self.assertIsNotNone(db.get(Conversation, active_empty_id))
        finally:
            db.close()


def _session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    testing_session = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
        class_=_DisposableSession,
    )
    return testing_session()


class _DisposableSession(Session):
    def close(self) -> None:
        bind = self.get_bind()
        super().close()
        bind.dispose()


if __name__ == "__main__":
    unittest.main()
