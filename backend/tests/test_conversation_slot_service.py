from types import SimpleNamespace

from app.services.conversation.slot_service import ConversationSlotService


def _context():
    return SimpleNamespace(slots={}, revision=1)


def test_slots_accept_multiple_fields_in_any_order_and_preserve_corrections():
    context = _context()
    service = ConversationSlotService()

    changed = service.apply_entities(
        context,
        {
            "amount": 5000,
            "monthly_income": 1800,
            "term_months": 24,
        },
    )
    assert set(changed) == {"amount", "monthly_income", "term_months"}
    assert service.value(context, "amount") == 5000

    service.apply_entities(context, {"term_months": 36})
    term_slot = context.slots["term_months"]
    assert term_slot["value"] == 36
    assert term_slot["history"][-1]["value"] == 24


def test_next_question_depends_on_missing_information_not_previous_state():
    context = _context()
    service = ConversationSlotService()
    service.set_slot(context, "privacy_consent", True, "GRANTED", "USER_MESSAGE")
    service.set_slot(
        context,
        "product_code",
        "CONSUMO_PERSONAL_DEMO",
        "CONFIRMED",
        "USER_MESSAGE",
    )
    service.set_slot(context, "national_id", "9900000001", "CONFIRMED", "USER_MESSAGE")

    assert service.next_required_field(context) == "bureau_consent"

    service.set_slot(context, "bureau_consent", False, "DECLINED", "USER_MESSAGE")
    service.set_slot(context, "full_name", "Persona Demo", "CONFIRMED", "USER_MESSAGE")
    service.set_slot(context, "age", 35, "CONFIRMED", "USER_MESSAGE")
    service.set_slot(context, "employment_status", "EMPLOYED", "CONFIRMED", "USER_MESSAGE")
    service.set_slot(context, "employment_tenure", 48, "CONFIRMED", "USER_MESSAGE")
    service.set_slot(context, "amount", 2000, "CONFIRMED", "USER_MESSAGE")
    service.set_slot(context, "term_months", 24, "CONFIRMED", "USER_MESSAGE")
    service.set_slot(context, "monthly_income", 1800, "CONFIRMED", "USER_MESSAGE")
    service.set_slot(context, "monthly_expenses", 700, "CONFIRMED", "USER_MESSAGE")
    service.set_slot(context, "existing_debt_payments", 150, "CONFIRMED", "USER_MESSAGE")
    service.set_slot(context, "pep_status", "NOT_PEP", "CONFIRMED", "USER_MESSAGE")

    assert service.next_required_field(context) is None
