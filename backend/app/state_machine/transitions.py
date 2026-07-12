from app.state_machine.states import ConversationState

STATE_TRANSITIONS: dict[ConversationState, list[ConversationState]] = {
    ConversationState.START: [
        ConversationState.ASK_NAME,
        ConversationState.ASK_AMOUNT,
        ConversationState.HANDOFF,
        ConversationState.END,
    ],
    ConversationState.ASK_NAME: [
        ConversationState.ASK_AMOUNT,
        ConversationState.ASK_TERM,
        ConversationState.ASK_INCOME,
        ConversationState.SHOW_RESULT,
        ConversationState.HANDOFF,
        ConversationState.END,
    ],
    ConversationState.ASK_AMOUNT: [
        ConversationState.ASK_TERM,
        ConversationState.ASK_INCOME,
        ConversationState.SHOW_RESULT,
        ConversationState.HANDOFF,
        ConversationState.END,
    ],
    ConversationState.ASK_TERM: [
        ConversationState.ASK_INCOME,
        ConversationState.SHOW_RESULT,
        ConversationState.HANDOFF,
        ConversationState.END,
    ],
    ConversationState.ASK_INCOME: [
        ConversationState.SHOW_RESULT,
        ConversationState.HANDOFF,
        ConversationState.END,
    ],
    ConversationState.SHOW_RESULT: [
        ConversationState.HANDOFF,
        ConversationState.END,
    ],
    ConversationState.HANDOFF: [
        ConversationState.END,
    ],
    ConversationState.END: [],
}

VALID_TRANSITIONS = STATE_TRANSITIONS


def is_valid_transition(current: ConversationState, next_state: ConversationState) -> bool:
    allowed = STATE_TRANSITIONS.get(current, [])
    return next_state in allowed


def get_allowed_transitions(state: ConversationState) -> list[ConversationState]:
    return STATE_TRANSITIONS.get(state, [])


def can_transition(current_state: str, next_state: str) -> bool:
    try:
        current = ConversationState(current_state)
        target = ConversationState(next_state)
        return is_valid_transition(current, target)
    except ValueError:
        return False
