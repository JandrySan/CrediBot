from __future__ import annotations

import hashlib
import re
import unicodedata
from decimal import Decimal

from app.repositories.consent_repository import ConsentRepository
from app.repositories.customer_financial_profile_repository import (
    CustomerFinancialProfileRepository,
)
from app.services.credit_bureau.profile_service import (
    CreditBureauProfileService,
    CreditBureauUnavailable,
)


class AdaptiveCreditFlow:
    PRIVACY_PURPOSE = "Orientar, simular y gestionar una precalificacion crediticia en CrediBot."
    BUREAU_PURPOSE = (
        "Consultar el historial crediticio simulado para una precalificacion informativa."
    )

    def __init__(self, db, slot_service):
        self.db = db
        self.slots = slot_service
        self.consents = ConsentRepository(db)
        self.profiles = CustomerFinancialProfileRepository(db)

    def handle_pending_consent(self, context, customer, conversation, text: str) -> bool:
        pending = context.pending_field
        if pending not in {"privacy_consent", "bureau_consent"}:
            return False
        answer = self._consent_answer(text)
        if answer is None:
            return False

        granted = answer == "GRANTED"
        consent_type = "DATA_PROCESSING" if pending == "privacy_consent" else "CREDIT_BUREAU"
        purpose = self.PRIVACY_PURPOSE if pending == "privacy_consent" else self.BUREAU_PURPOSE
        self.consents.record(
            customer_id=customer.id,
            conversation_id=conversation.id,
            consent_type=consent_type,
            status=answer,
            purpose=purpose,
            evidence_hash=hashlib.sha256(text.encode("utf-8")).hexdigest(),
        )
        self.slots.set_slot(
            context,
            pending,
            granted,
            "GRANTED" if granted else "DECLINED",
            "USER_MESSAGE",
        )
        context.pending_field = None
        if pending == "privacy_consent" and not granted:
            context.active_goal = "INFORMATION_ONLY"
        return True

    def handle_pending_name_confirmation(self, context, customer, text: str) -> str | None:
        if context.pending_field != "full_name":
            return None
        if self.slots.status(context, "full_name") != "PROPOSED":
            return None

        answer = self._consent_answer(text)
        if answer is None:
            return None
        if answer == "DECLINED":
            self.slots.reject_slot(context, "full_name")
            customer.full_name = None
            self.db.flush()
            return "REJECTED"

        confirmed_name = self.slots.value(context, "full_name")
        self.slots.set_slot(
            context,
            "full_name",
            confirmed_name,
            "CONFIRMED",
            "USER_CONFIRMATION",
        )
        customer.full_name = confirmed_name
        context.pending_field = None
        self.db.flush()
        return "CONFIRMED"

    def apply_entities(self, context, customer, application, entities: dict) -> None:
        self.slots.apply_entities(context, entities)
        customer.national_id = self.slots.value(context, "national_id") or customer.national_id
        if self.slots.status(context, "full_name") in {"CONFIRMED", "VERIFIED"}:
            customer.full_name = self.slots.value(context, "full_name") or customer.full_name

        application.amount = self._optional_decimal(self.slots.value(context, "amount"))
        application.term_months = self._optional_int(self.slots.value(context, "term_months"))
        application.monthly_income = self._optional_decimal(
            self.slots.value(context, "monthly_income")
        )
        application.purpose = self.slots.value(context, "purpose")

        profile = self.profiles.get_or_create(customer.id)
        employment = self.slots.value(context, "employment_status")
        tenure = self._optional_int(self.slots.value(context, "employment_tenure"))
        self.profiles.update(
            profile,
            employment_status=employment,
            job_tenure_months=tenure if employment == "EMPLOYED" else None,
            business_tenure_months=tenure if employment == "SELF_EMPLOYED" else None,
            monthly_net_income=self._optional_decimal(self.slots.value(context, "monthly_income")),
            other_monthly_income=self._optional_decimal(
                self.slots.value(context, "other_monthly_income")
            ),
            monthly_living_expenses=self._optional_decimal(
                self.slots.value(context, "monthly_expenses")
            ),
            existing_monthly_debt_payments=self._optional_decimal(
                self.slots.value(context, "existing_debt_payments")
            ),
            pep_status=self.slots.value(context, "pep_status", "UNKNOWN"),
        )
        self.db.flush()

    def hydrate_from_bureau(self, context, customer) -> dict | None:
        if self.slots.status(context, "bureau_consent") != "GRANTED":
            return None
        identifier = self.slots.value(context, "national_id")
        if not identifier:
            return None
        try:
            bureau = CreditBureauProfileService(self.db).find_profile(identifier)
        except CreditBureauUnavailable:
            return None
        if not bureau:
            return None

        mappings = {
            "age": "age",
            "employment_status": "employment_status",
            "monthly_income": "reported_monthly_income",
            "other_monthly_income": "other_monthly_income",
            "monthly_expenses": "monthly_living_expenses",
            "existing_debt_payments": "total_monthly_debt_payment",
            "pep_status": "pep_status",
            "identity_verified": "identity_verified",
            "credit_score": "credit_score",
            "max_days_past_due": "max_days_past_due",
            "recent_inquiries_6m": "recent_inquiries_6m",
        }
        self._merge_bureau_name(context, bureau.get("full_name"))
        for slot_name, bureau_name in mappings.items():
            value = bureau.get(bureau_name)
            if value is not None:
                self.slots.verify_slot(context, slot_name, value)

        employment = bureau.get("employment_status")
        tenure = (
            bureau.get("business_tenure_months")
            if employment == "SELF_EMPLOYED"
            else bureau.get("job_tenure_months")
        )
        if tenure is not None:
            self.slots.verify_slot(context, "employment_tenure", tenure)
        return bureau

    def _merge_bureau_name(self, context, bureau_name) -> None:
        if not bureau_name:
            return
        current = (context.slots or {}).get("full_name")
        if current is None:
            self.slots.set_slot(
                context,
                "full_name",
                bureau_name,
                "PROPOSED",
                "CREDIT_BUREAU",
            )
            return

        current_value = str(current.get("value") or "")
        if current.get("status") == "PROPOSED":
            return
        if current.get("status") == "REJECTED":
            if current_value != str(bureau_name):
                self.slots.set_slot(
                    context,
                    "full_name",
                    bureau_name,
                    "PROPOSED",
                    "CREDIT_BUREAU",
                )
            return
        if current_value == str(bureau_name):
            self.slots.verify_slot(context, "full_name", bureau_name)
            return
        if current.get("source") in {"USER_MESSAGE", "USER_CONFIRMATION"}:
            return
        self.slots.verify_slot(context, "full_name", bureau_name)

    @staticmethod
    def privacy_question() -> str:
        return (
            "Antes de empezar, necesito tu permiso para usar los datos que compartas "
            "solo en esta precalificacion. Es una simulacion, no una aprobacion final, "
            "y puedes detenerte o pedir un asesor cuando quieras.\n\n"
            "¿Aceptas continuar? Responde si o no."
        )

    @staticmethod
    def bureau_question() -> str:
        return (
            "¿Me autorizas a consultar tu historial en la central de riesgo simulada? "
            "Revisare puntaje, deudas y pagos solo para esta precalificacion.\n\n"
            "Responde si o no. Si dices no, igual podemos continuar con los datos que me des."
        )

    @staticmethod
    def _consent_answer(text: str) -> str | None:
        normalized = "".join(
            character
            for character in unicodedata.normalize("NFD", (text or "").lower())
            if unicodedata.category(character) != "Mn"
        )
        normalized = re.sub(r"[^a-z\s]", " ", normalized)
        tokens = set(normalized.split())
        if tokens & {"si", "acepto", "autorizo", "confirmo", "continuar", "continua"}:
            return "GRANTED"
        if tokens & {"no", "rechazo", "declino", "cancelar", "cancela"}:
            return "DECLINED"
        return None

    @staticmethod
    def _optional_decimal(value) -> Decimal | None:
        return None if value is None else Decimal(str(value))

    @staticmethod
    def _optional_int(value) -> int | None:
        return None if value is None else int(value)
