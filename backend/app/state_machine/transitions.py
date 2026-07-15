from app.state_machine.states import ConversationState

COLLECTION_STATES = tuple(
    state
    for state in ConversationState
    if state not in {ConversationState.HANDOFF, ConversationState.END}
)

STATE_TRANSITIONS: dict[ConversationState, list[ConversationState]] = {
    state: [target for target in COLLECTION_STATES if target != state]
    + [ConversationState.HANDOFF, ConversationState.END]
    for state in COLLECTION_STATES
}
STATE_TRANSITIONS[ConversationState.HANDOFF] = [ConversationState.END]
STATE_TRANSITIONS[ConversationState.END] = []


def is_valid_transition(current: ConversationState, next_state: ConversationState) -> bool:
    return next_state in STATE_TRANSITIONS.get(current, []) or current == next_state


def get_allowed_transitions(state: ConversationState) -> list[ConversationState]:
    return STATE_TRANSITIONS.get(state, [])


def can_transition(current_state: str, next_state: str) -> bool:
    try:
        return is_valid_transition(ConversationState(current_state), ConversationState(next_state))
    except ValueError:
        return False
