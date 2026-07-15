from types import SimpleNamespace

from app.services.conversation.conversation_state_service import ConversationStateService
from app.services.conversation.credit_application_service import CreditApplicationService
from app.services.conversation.input_extractor import ConversationInputExtractor
from app.services.conversation.policy import ConversationPolicy
from app.services.conversation.response_builder import ConversationResponseBuilder


def _responses() -> ConversationResponseBuilder:
    return ConversationResponseBuilder()


def _input() -> ConversationInputExtractor:
    return ConversationInputExtractor(ConversationStateService(), CreditApplicationService())


def test_sanitize_response_removes_de_nada_if_user_did_not_thank():
    cleaned = _responses().sanitize(
        response="De nada. En cuantos meses te gustaria pagarlo?",
        user_text="Quiero pagarlo en 24",
    )
    assert cleaned == "En cuantos meses te gustaria pagarlo?"


def test_sanitize_response_keeps_de_nada_if_user_thanked():
    cleaned = _responses().sanitize(
        response="De nada, seguimos con tu solicitud.",
        user_text="gracias por la ayuda",
    )
    assert cleaned.startswith("De nada")


def test_result_response_integrates_user_data_in_same_message():
    customer = SimpleNamespace(full_name="Juan Perez", national_id="9990000001")
    application = SimpleNamespace(amount=1200, term_months=24, monthly_income=900)
    text = _responses().build_result_response(
        evaluation={"result": "PREAPROBADO", "reason": "Cumple reglas base."},
        customer=customer,
        application=application,
    )
    assert "preaprobado" in text
    assert "PREAPROBADO" not in text
    assert "Juan Perez" in text
    assert "9990000001" in text
    assert "24 meses" in text
    assert "ingresos mensuales" in text


def test_question_for_national_id_explains_central_risk_lookup():
    customer = SimpleNamespace(full_name=None, national_id=None)
    application = SimpleNamespace(amount=None, term_months=None, monthly_income=None)
    text = _responses().question_for_field("national_id", customer, application)
    assert "cedula" in text.lower()
    assert "10 digitos" in text.lower()
    assert "central de riesgo" in text.lower()


def test_question_for_name_is_cordial_and_requests_full_name():
    customer = SimpleNamespace(full_name=None, national_id="9990000999")
    application = SimpleNamespace(amount=None, term_months=None, monthly_income=None)
    text = _responses().question_for_field("full_name", customer, application)
    assert "no encontre" in text.lower()
    assert "nombre completo" in text.lower()


def test_question_for_amount_mentions_pleasure_and_name():
    customer = SimpleNamespace(full_name="Carlos")
    application = SimpleNamespace(amount=None, term_months=None, monthly_income=None)
    text = _responses().question_for_field("amount", customer, application)
    assert "Es un gusto hablar contigo, Carlos" in text
    assert "monto" in text.lower()


def test_plain_greeting_gets_welcome_without_requesting_name():
    text = ConversationPolicy.welcome_response()
    assert "en que te puedo ayudar" in text.lower()
    assert "nombre completo" not in text.lower()


def test_plain_greeting_detection_accepts_accented_text():
    assert ConversationPolicy.is_plain_greeting("Hola, buen dia")
    assert ConversationPolicy.is_plain_greeting("Hola, buen día")
    assert not ConversationPolicy.is_plain_greeting("Hola, quiero un credito")


def test_preference_text_is_not_valid_person_name():
    assert not CreditApplicationService.is_valid_person_name("Respondem por audio")
    assert not CreditApplicationService.is_valid_person_name("responde en texto")
    assert CreditApplicationService.is_valid_person_name("Carlos Pico")


def test_extract_name_rejects_audio_preference_text():
    extractor = _input()
    assert extractor.extract_name("Respondem por audio") is None
    assert extractor.extract_name("Carlos Pico") == "Carlos Pico"


def test_person_name_does_not_trigger_handoff():
    assert not ConversationPolicy.is_handoff_requested(
        "Persona Sintetica Demo",
        {"intent": "credito"},
    )
    assert ConversationPolicy.is_handoff_requested(
        "Quiero hablar con una persona real",
        {"intent": "credito"},
    )
