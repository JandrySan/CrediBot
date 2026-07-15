from app.state_machine.states import ConversationState
from app.state_machine.transitions import STATE_TRANSITIONS


class ConversationStateService:
    def get_next_required_field(self, customer, application) -> str | None:
        if not getattr(customer, "national_id", None):
            return "national_id"

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
            "privacy_consent": ConversationState.ASK_PRIVACY_CONSENT.value,
            "product_code": ConversationState.ASK_PRODUCT.value,
            "national_id": ConversationState.ASK_NATIONAL_ID.value,
            "bureau_consent": ConversationState.ASK_BUREAU_CONSENT.value,
            "full_name": ConversationState.ASK_NAME.value,
            "age": ConversationState.ASK_AGE.value,
            "employment_status": ConversationState.ASK_EMPLOYMENT.value,
            "employment_tenure": ConversationState.ASK_EMPLOYMENT_TENURE.value,
            "amount": ConversationState.ASK_AMOUNT.value,
            "term_months": ConversationState.ASK_TERM.value,
            "monthly_income": ConversationState.ASK_INCOME.value,
            "monthly_expenses": ConversationState.ASK_EXPENSES.value,
            "existing_debt_payments": ConversationState.ASK_DEBTS.value,
            "pep_status": ConversationState.ASK_PEP_STATUS.value,
        }

        return mapping.get(field, ConversationState.START.value)

    def get_allowed_transition_names(self, current_state: str) -> list[str]:
        try:
            state = ConversationState(current_state)
            transitions = STATE_TRANSITIONS.get(state, [])
            return [t.value for t in transitions]
        except ValueError:
            return []
