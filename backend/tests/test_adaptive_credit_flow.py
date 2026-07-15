from contextlib import contextmanager
from datetime import date
from decimal import Decimal
from types import SimpleNamespace

from sqlalchemy import func, select

from app.database.session import SessionLocal
from app.models.consent_record import ConsentRecord
from app.models.conversation_context import ConversationContext
from app.models.credit_application import CreditApplication
from app.models.credit_decision import CreditDecision
from app.models.credit_policy import CreditPolicyVersion
from app.models.credit_product import CreditProduct
from app.services.conversation.orchestrator import ConversationOrchestrator


@contextmanager
def _rollback_session():
    db = SessionLocal()
    transaction = db.begin()
    try:
        yield db
    finally:
        transaction.rollback()
        db.close()


def _seed_product_and_policy(db) -> None:
    product = CreditProduct(
        code="CONSUMO_PERSONAL_DEMO",
        name="Consumo adaptable",
        segment="CONSUMPTION",
        description="Producto para prueba adaptable.",
        currency="USD",
        min_amount=Decimal("500"),
        max_amount=Decimal("30000"),
        min_term_months=6,
        max_term_months=60,
        effective_annual_rate=Decimal("15.5"),
        max_effective_annual_rate=Decimal("16.77"),
        amortization_type="FRENCH",
        payment_frequency="MONTHLY",
        is_active=True,
        is_demo=True,
        effective_from=date(2026, 1, 1),
    )
    db.add(product)
    db.add(
        CreditPolicyVersion(
            code="ADAPTIVE_TEST",
            name="Politica adaptable",
            status="ACTIVE",
            description="Politica para probar la conversacion.",
            is_demo=True,
            effective_from=date(2026, 1, 1),
        )
    )
    db.flush()


def _disable_external_ai(orchestrator: ConversationOrchestrator) -> None:
    fields = {
        "product_code": None,
        "national_id": None,
        "full_name": None,
        "age": None,
        "employment_status": None,
        "employment_tenure": None,
        "amount": None,
        "term_months": None,
        "monthly_income": None,
        "other_monthly_income": None,
        "monthly_expenses": None,
        "existing_debt_payments": None,
        "pep_status": None,
        "purpose": None,
    }
    orchestrator.ai = SimpleNamespace(
        analyze_message=lambda _text: {"intent": "credito", **fields},
        get_model_name=lambda: "deterministic-test",
        improve_response=lambda message, last_user_message="": message,
        generate_whatsapp_reply=lambda **_kwargs: "Respuesta informativa desde la base.",
    )


def test_adaptive_flow_accepts_short_answers_and_corrections_without_restarting():
    with _rollback_session() as db:
        _seed_product_and_policy(db)
        orchestrator = ConversationOrchestrator(db)
        _disable_external_ai(orchestrator)
        phone = "+593980999991"

        assert "Aceptas continuar" in orchestrator.handle_text_message(phone, "Quiero un prestamo")
        assert "personal o negocio" in orchestrator.handle_text_message(phone, "si").lower()
        assert "cedula" in orchestrator.handle_text_message(phone, "consumo").lower()
        assert "autorizas" in orchestrator.handle_text_message(phone, "9900000001").lower()
        assert "nombre completo" in orchestrator.handle_text_message(phone, "no").lower()
        assert "edad" in orchestrator.handle_text_message(phone, "Persona Sintetica Demo").lower()
        assert "ingresos" in orchestrator.handle_text_message(phone, "35").lower()
        assert "Cuanto tiempo" in orchestrator.handle_text_message(phone, "empleado")
        assert "cuanto dinero" in orchestrator.handle_text_message(phone, "24 meses").lower()
        assert "cuantos meses" in orchestrator.handle_text_message(phone, "5000").lower()
        assert "cuanto recibes" in orchestrator.handle_text_message(phone, "36").lower()
        assert "gastas al mes" in orchestrator.handle_text_message(phone, "1800").lower()
        assert "otras deudas" in orchestrator.handle_text_message(phone, "700").lower()
        assert "cargo publico" in orchestrator.handle_text_message(phone, "100").lower()

        result = orchestrator.handle_text_message(phone, "no")
        assert "simulacion informativa" in result.lower()
        assert "cuota estimada" in result.lower()

        context = db.scalar(select(ConversationContext))
        assert context.slots["employment_tenure"]["value"] == 24
        assert context.slots["term_months"]["value"] == 36
        assert db.scalar(select(func.count(ConsentRecord.id))) == 2
        assert db.scalar(select(CreditApplication)).status == "SIMULATION_ONLY"
        assert db.scalar(select(func.count(CreditDecision.id))) == 1

        corrected = orchestrator.handle_text_message(phone, "El plazo es 48 meses")
        assert "simulacion informativa" in corrected.lower()
        assert context.slots["term_months"]["value"] == 48
        assert context.slots["term_months"]["history"][-1]["value"] == 36
        assert db.scalar(select(func.count(CreditDecision.id))) == 2


def test_credit_bureau_tool_is_hidden_until_authorization():
    class Gateway:
        def __init__(self):
            self.tools = []

        def generate_with_tools(self, messages, tools, **_kwargs):
            _ = messages
            self.tools = tools
            return "Respuesta", []

    with SessionLocal() as db:
        orchestrator = ConversationOrchestrator(db)
        gateway = Gateway()
        orchestrator.ai.gateway = gateway

        orchestrator.ai.generate_whatsapp_reply("Revisa mi score", db=db)
        names = {spec["function"]["name"] for spec in gateway.tools}
        assert "consultar_historial_crediticio" not in names

        orchestrator.ai.generate_whatsapp_reply(
            "Revisa mi score",
            db=db,
            allow_credit_bureau=True,
        )
        names = {spec["function"]["name"] for spec in gateway.tools}
        assert "consultar_historial_crediticio" in names
