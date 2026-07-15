from sqlalchemy import and_, func, not_, or_
from sqlalchemy.orm import Session

from app.models.conversation import Conversation
from app.models.credit_application import CreditApplication
from app.models.customer import Customer
from app.models.message import Message
from app.repositories.conversation_repository import ABANDONED_CONVERSATION_RESULTS
from app.schemas.dashboard import (
    ConversationMessage,
    ConversationSummary,
    DashboardStats,
)


class DashboardQueryService:
    def __init__(self, db: Session):
        self.db = db

    def get_stats(self) -> DashboardStats:
        message_counts = self._message_count_subquery()
        message_count = func.coalesce(message_counts.c.message_count, 0)
        visible = (
            self.db.query(Conversation)
            .outerjoin(
                message_counts,
                message_counts.c.conversation_id == Conversation.id,
            )
            .filter(self._visible_filter(message_count))
        )
        return DashboardStats(
            customers=self.db.query(Customer).count(),
            conversations=visible.count(),
            active_conversations=visible.filter(Conversation.status == "ACTIVE").count(),
            handoff_conversations=visible.filter(Conversation.status == "HANDOFF").count(),
            closed_conversations=visible.filter(Conversation.status == "CLOSED").count(),
            preapproved=self._application_count("PREAPROBADO"),
            observed=self._application_count("OBSERVADO"),
        )

    def get_conversations(self) -> list[ConversationSummary]:
        message_counts = self._message_count_subquery()
        message_count = func.coalesce(message_counts.c.message_count, 0)
        latest_applications = (
            self.db.query(
                CreditApplication.customer_id,
                func.max(CreditApplication.id).label("max_id"),
            )
            .group_by(CreditApplication.customer_id)
            .subquery()
        )
        rows = (
            self.db.query(Conversation, Customer, CreditApplication)
            .join(Customer, Conversation.customer_id == Customer.id)
            .outerjoin(
                message_counts,
                message_counts.c.conversation_id == Conversation.id,
            )
            .outerjoin(
                latest_applications,
                latest_applications.c.customer_id == Customer.id,
            )
            .outerjoin(
                CreditApplication,
                CreditApplication.id == latest_applications.c.max_id,
            )
            .filter(self._visible_filter(message_count))
            .order_by(Conversation.id.desc())
            .all()
        )
        return [self._conversation_summary(*row) for row in rows]

    def get_messages(self, conversation_id: int) -> list[ConversationMessage]:
        rows = (
            self.db.query(Message)
            .filter(Message.conversation_id == conversation_id)
            .order_by(Message.id.asc())
            .all()
        )
        return [
            ConversationMessage(
                id=message.id,
                direction=message.direction,
                type=message.message_type,
                content=message.content,
                created_at=message.created_at,
            )
            for message in rows
        ]

    def _application_count(self, result: str) -> int:
        return self.db.query(CreditApplication).filter(CreditApplication.result == result).count()

    def _message_count_subquery(self):
        return (
            self.db.query(
                Message.conversation_id,
                func.count(Message.id).label("message_count"),
            )
            .group_by(Message.conversation_id)
            .subquery()
        )

    @staticmethod
    def _visible_filter(message_count):
        return not_(
            and_(
                Conversation.status == "CLOSED",
                or_(
                    Conversation.result.in_(ABANDONED_CONVERSATION_RESULTS),
                    message_count == 0,
                ),
            )
        )

    @staticmethod
    def _conversation_summary(
        conversation: Conversation,
        customer: Customer,
        application: CreditApplication | None,
    ) -> ConversationSummary:
        return ConversationSummary(
            conversation_id=conversation.id,
            customer_id=customer.id,
            phone_number=customer.phone_number,
            national_id=customer.national_id,
            full_name=customer.full_name,
            state=conversation.current_state,
            status=conversation.status,
            conversation_result=conversation.result,
            credit_amount=(
                float(application.amount)
                if application and application.amount is not None
                else None
            ),
            term_months=application.term_months if application else None,
            monthly_income=(
                float(application.monthly_income)
                if application and application.monthly_income is not None
                else None
            ),
            credit_result=application.result if application else None,
            credit_reason=application.reason if application else None,
            created_at=conversation.created_at,
        )
