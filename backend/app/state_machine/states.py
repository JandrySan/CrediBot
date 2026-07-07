from enum import Enum


class ConversationState(str, Enum):
    START = "START"
    ASK_NAME = "ASK_NAME"
    ASK_AMOUNT = "ASK_AMOUNT"
    ASK_TERM = "ASK_TERM"
    ASK_INCOME = "ASK_INCOME"
    SHOW_RESULT = "SHOW_RESULT"
    HANDOFF = "HANDOFF"
    END = "END"