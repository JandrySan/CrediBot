from app.state_machine.states import ConversationState


class ConversationStateService:
    def get_next_required_field(self, customer, application) -> str | None:
        if not customer.full_name:
            return "full_name"

        if not application.amount:
            return "amount"

        if not application.term_months:
            return "term_months"

        if not application.monthly_income:
            return "monthly_income"

        return None

    def state_for_missing_field(self, field: str) -> str:
        mapping = {
            "full_name": ConversationState.ASK_NAME.value,
            "amount": ConversationState.ASK_AMOUNT.value,
            "term_months": ConversationState.ASK_TERM.value,
            "monthly_income": ConversationState.ASK_INCOME.value,
        }

        return mapping.get(field, ConversationState.START.value)