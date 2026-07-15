from types import SimpleNamespace

from app.services.conversation.adaptive_flow import AdaptiveCreditFlow
from app.services.conversation.slot_service import ConversationSlotService


class _Database:
    def flush(self):
        return None


def _context():
    return SimpleNamespace(slots={}, revision=0, pending_field="full_name")


def test_bureau_name_must_be_confirmed_before_it_becomes_available():
    context = _context()
    customer = SimpleNamespace(full_name=None)
    flow = AdaptiveCreditFlow(_Database(), ConversationSlotService())
    flow.slots.set_slot(context, "privacy_consent", True, "GRANTED", "USER_MESSAGE")
    flow.slots.set_slot(
        context,
        "product_code",
        "CONSUMO_PERSONAL_DEMO",
        "CONFIRMED",
        "USER_MESSAGE",
    )
    flow.slots.set_slot(context, "national_id", "9900000001", "CONFIRMED", "USER_MESSAGE")
    flow.slots.set_slot(context, "bureau_consent", True, "GRANTED", "USER_MESSAGE")

    flow._merge_bureau_name(context, "Juan Perez")

    assert flow.slots.status(context, "full_name") == "PROPOSED"
    assert flow.slots.next_required_field(context) == "full_name"

    result = flow.handle_pending_name_confirmation(context, customer, "Si, es correcto")

    assert result == "CONFIRMED"
    assert flow.slots.status(context, "full_name") == "CONFIRMED"
    assert customer.full_name == "Juan Perez"


def test_rejected_bureau_name_is_not_proposed_again():
    context = _context()
    customer = SimpleNamespace(full_name=None)
    flow = AdaptiveCreditFlow(_Database(), ConversationSlotService())
    flow._merge_bureau_name(context, "Nombre Incorrecto")

    result = flow.handle_pending_name_confirmation(context, customer, "No")
    flow._merge_bureau_name(context, "Nombre Incorrecto")

    assert result == "REJECTED"
    assert flow.slots.status(context, "full_name") == "REJECTED"
    assert customer.full_name is None


def test_valid_bureau_name_can_replace_a_previous_invalid_rejected_value():
    context = _context()
    flow = AdaptiveCreditFlow(_Database(), ConversationSlotService())
    flow.slots.set_slot(
        context,
        "full_name",
        "Simulador de Credito",
        "REJECTED",
        "SYSTEM_VALIDATION",
    )

    flow._merge_bureau_name(context, "Juan Perez")

    assert flow.slots.status(context, "full_name") == "PROPOSED"
    assert flow.slots.value(context, "full_name") == "Juan Perez"
