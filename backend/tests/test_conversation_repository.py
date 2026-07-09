import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

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


if __name__ == "__main__":
    unittest.main()
