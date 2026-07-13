from types import SimpleNamespace

from app.services.conversation.orchestrator import ConversationOrchestrator
from app.services.conversation.credit_application_service import CreditApplicationService


def _build_orchestrator_for_unit_tests() -> ConversationOrchestrator:
    orchestrator = ConversationOrchestrator.__new__(ConversationOrchestrator)
    orchestrator.ai = SimpleNamespace(
        improve_response=lambda message, last_user_message="": message,
    )
    return orchestrator


def test_sanitize_response_removes_de_nada_if_user_did_not_thank():
    orchestrator = _build_orchestrator_for_unit_tests()

    cleaned = orchestrator._sanitize_response(
        response="De nada. En cuantos meses te gustaria pagarlo?",
        user_text="Quiero pagarlo en 24",
    )

    assert cleaned == "En cuantos meses te gustaria pagarlo?"


def test_sanitize_response_keeps_de_nada_if_user_thanked():
    orchestrator = _build_orchestrator_for_unit_tests()

    cleaned = orchestrator._sanitize_response(
        response="De nada, seguimos con tu solicitud.",
        user_text="gracias por la ayuda",
    )

    assert cleaned.startswith("De nada")


def test_result_response_integrates_user_data_in_same_message():
    orchestrator = _build_orchestrator_for_unit_tests()

    customer = SimpleNamespace(full_name="Juan Perez")
    application = SimpleNamespace(amount=1200, term_months=24, monthly_income=900)

    text = orchestrator._build_result_response(
        evaluation={"result": "PREAPROBADO", "reason": "Cumple reglas base."},
        customer=customer,
        application=application,
    )

    assert "preaprobado" in text
    assert "PREAPROBADO" not in text
    assert "Juan Perez" in text
    assert "24 meses" in text
    assert "ingresos mensuales" in text


def test_question_for_name_is_cordial_and_requests_full_name():
    orchestrator = _build_orchestrator_for_unit_tests()

    customer = SimpleNamespace(full_name=None)
    application = SimpleNamespace(amount=None, term_months=None, monthly_income=None)

    text = orchestrator._question_for_field("full_name", customer, application)

    assert "que gusto saludarte" in text.lower()
    assert "nombre completo" in text.lower()


def test_question_for_amount_mentions_pleasure_and_name():
    orchestrator = _build_orchestrator_for_unit_tests()

    customer = SimpleNamespace(full_name="Carlos")
    application = SimpleNamespace(amount=None, term_months=None, monthly_income=None)

    text = orchestrator._question_for_field("amount", customer, application)

    assert "Es un gusto hablar contigo, Carlos" in text
    assert "monto" in text.lower()


def test_plain_greeting_gets_welcome_without_requesting_name():
    orchestrator = _build_orchestrator_for_unit_tests()

    text = orchestrator._build_welcome_response()

    assert "en que te puedo ayudar" in text.lower()
    assert "nombre completo" not in text.lower()


def test_plain_greeting_detection_accepts_accented_text():
    orchestrator = _build_orchestrator_for_unit_tests()

    assert orchestrator._is_plain_greeting("Hola, buen dia")
    assert orchestrator._is_plain_greeting("Hola, buen día")
    assert not orchestrator._is_plain_greeting("Hola, quiero un credito")


def test_preference_text_is_not_valid_person_name():
    assert not CreditApplicationService.is_valid_person_name("Respondem por audio")
    assert not CreditApplicationService.is_valid_person_name("responde en texto")
    assert CreditApplicationService.is_valid_person_name("Carlos Pico")


def test_extract_name_rejects_audio_preference_text():
    orchestrator = _build_orchestrator_for_unit_tests()
    orchestrator.credit_service = CreditApplicationService()

    assert orchestrator._extract_name("Respondem por audio") is None
    assert orchestrator._extract_name("Carlos Pico") == "Carlos Pico"
