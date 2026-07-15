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


def test_result_response_is_short_and_does_not_repeat_sensitive_profile():
    customer = SimpleNamespace(full_name="Juan Perez", national_id="9990000001")
    application = SimpleNamespace(amount=1200, term_months=24, monthly_income=900)
    text = _responses().build_result_response(
        evaluation={
            "result": "NEEDS_INFORMATION",
            "estimated_installment": 58.25,
            "reason": "Explicacion extensa de respaldo.",
            "rule_results": [
                {
                    "code": "IDENTITY_VERIFIED",
                    "outcome": "NEEDS_INFORMATION",
                    "passed": False,
                    "explanation": "La identidad debe verificarse.",
                }
            ],
        },
        customer=customer,
        application=application,
    )
    assert "pendiente de informacion" in text
    assert "Cuota estimada: $58.25" in text
    assert "24 meses" in text
    assert "Falta verificar tu identidad" in text
    assert "Juan Perez" not in text
    assert "9990000001" not in text
    assert "Motivo:" not in text


def test_result_response_limits_reasons_to_three_clear_points():
    customer = SimpleNamespace(full_name="Juan Perez", national_id="9990000001")
    application = SimpleNamespace(amount=5000, term_months=24, monthly_income=2000)
    failures = [
        {
            "code": code,
            "outcome": outcome,
            "passed": False,
            "explanation": code,
        }
        for code, outcome in (
            ("IDENTITY_VERIFIED", "NEEDS_INFORMATION"),
            ("MINIMUM_CREDIT_SCORE", "MANUAL_REVIEW"),
            ("NO_ACTIVE_SEVERE_DELINQUENCY", "NOT_PREQUALIFIED"),
            ("MAXIMUM_RECENT_INQUIRIES", "MANUAL_REVIEW"),
        )
    ]
    text = _responses().build_result_response(
        evaluation={
            "result": "NOT_PREQUALIFIED",
            "estimated_installment": 241.24,
            "rule_results": failures,
        },
        customer=customer,
        application=application,
    )
    assert text.count("•") == 3
    assert "mora importante" in text


def test_question_for_national_id_explains_authorization_before_history_lookup():
    customer = SimpleNamespace(full_name=None, national_id=None)
    application = SimpleNamespace(amount=None, term_months=None, monthly_income=None)
    text = _responses().question_for_field("national_id", customer, application)
    assert "cedula" in text.lower()
    assert "10 digitos" in text.lower()
    assert "historial" in text.lower()
    assert "autorizacion" in text.lower()


def test_question_for_name_is_cordial_and_requests_full_name():
    customer = SimpleNamespace(full_name=None, national_id="9990000999")
    application = SimpleNamespace(amount=None, term_months=None, monthly_income=None)
    text = _responses().question_for_field("full_name", customer, application)
    assert "nombre completo" in text.lower()
    assert "Maria Lopez" in text


def test_bureau_name_is_presented_for_confirmation():
    customer = SimpleNamespace(full_name=None, national_id="9990000999")
    application = SimpleNamespace(amount=None, term_months=None, monthly_income=None)
    text = _responses().question_for_field(
        "full_name",
        customer,
        application,
        suggested_value="Juan Perez",
    )
    assert "Juan Perez" in text
    assert "Es correcto" in text


def test_question_for_amount_mentions_pleasure_and_name():
    customer = SimpleNamespace(full_name="Carlos")
    application = SimpleNamespace(amount=None, term_months=None, monthly_income=None)
    text = _responses().question_for_field("amount", customer, application)
    assert "Perfecto, Carlos" in text
    assert "Cuanto dinero" in text


def test_plain_greeting_gets_welcome_without_requesting_name():
    text = ConversationPolicy.welcome_response()
    assert "escribe lo que necesitas" in text.lower()
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
    assert extractor.extract_name("Simulador de Credito") is None
    assert extractor.extract_name("Quiero continuar") is None
    assert extractor.extract_name("Carlos Pico") == "Carlos Pico"


def test_contextual_name_filter_discards_ai_hallucination_from_credit_request():
    extractor = _input()
    data = extractor.enrich_pending_field(
        "Ahora quiero continuar con una simulacion para saber si soy apto",
        None,
        {"full_name": "Simulador de Credito", "intent": "credito"},
    )
    assert "full_name" not in data


def test_contextual_name_filter_accepts_bare_or_explicit_person_name():
    extractor = _input()
    bare = extractor.enrich_pending_field(
        "Maria Fernanda Lopez",
        "full_name",
        {"full_name": None},
    )
    explicit = extractor.enrich_pending_field(
        "Me llamo Maria Fernanda Lopez y quiero un credito",
        None,
        {"full_name": "Credito Personal"},
    )
    assert bare["full_name"] == "Maria Fernanda Lopez"
    assert explicit["full_name"] == "Maria Fernanda Lopez"


def test_name_denial_is_not_interpreted_as_a_new_name():
    extractor = _input()
    data = extractor.enrich_pending_field(
        "No me llamo yo simulador de credito",
        "full_name",
        {"full_name": "Simulador de Credito"},
    )
    assert extractor.is_name_denial("No me llamo yo simulador de credito")
    assert "full_name" not in data


def test_name_denial_can_include_the_real_correction():
    extractor = _input()
    data = extractor.enrich_pending_field(
        "No me llamo Juan Perez; me llamo Maria Lopez",
        "full_name",
        {"full_name": "Juan Perez"},
    )
    assert data["full_name"] == "Maria Lopez"


def test_person_name_does_not_trigger_handoff():
    assert not ConversationPolicy.is_handoff_requested(
        "Persona Sintetica Demo",
        {"intent": "credito"},
    )
    assert ConversationPolicy.is_handoff_requested(
        "Quiero hablar con una persona real",
        {"intent": "credito"},
    )


def test_intent_fallback_does_not_treat_the_word_persona_as_handoff():
    from app.services.ai.intent_detector import IntentDetector

    assert IntentDetector()._fallback("Soy una persona independiente") != "asesor"
