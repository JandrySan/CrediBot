from datetime import date

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.credit_policy import CreditPolicyRule, CreditPolicyVersion
from app.models.credit_product import CreditProduct, CreditProductRequirement


class CreditCatalogRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_active_products(self, as_of: date | None = None) -> list[CreditProduct]:
        effective_date = as_of or date.today()
        statement = (
            select(CreditProduct)
            .where(
                CreditProduct.is_active.is_(True),
                CreditProduct.effective_from <= effective_date,
                or_(
                    CreditProduct.effective_to.is_(None),
                    CreditProduct.effective_to >= effective_date,
                ),
            )
            .order_by(CreditProduct.id)
        )
        return list(self.db.scalars(statement))

    def get_product(self, code: str) -> CreditProduct | None:
        normalized = (code or "").strip().upper()
        if not normalized:
            return None
        return self.db.scalar(
            select(CreditProduct).where(
                CreditProduct.code == normalized,
                CreditProduct.is_active.is_(True),
            )
        )

    def resolve_product(self, value: str | None) -> CreditProduct | None:
        normalized = (value or "").strip().lower()
        if not normalized:
            products = self.list_active_products()
            return products[0] if products else None

        product = self.get_product(normalized.upper())
        if product:
            return product

        aliases = {
            "consumo": "CONSUMO_PERSONAL_DEMO",
            "personal": "CONSUMO_PERSONAL_DEMO",
            "prestamo": "CONSUMO_PERSONAL_DEMO",
            "préstamo": "CONSUMO_PERSONAL_DEMO",
            "microcredito": "MICROCREDITO_MINORISTA_DEMO",
            "microcrédito": "MICROCREDITO_MINORISTA_DEMO",
            "negocio": "MICROCREDITO_MINORISTA_DEMO",
        }
        for alias, code in aliases.items():
            if alias in normalized:
                return self.get_product(code)
        return None

    def list_requirements(
        self,
        product_id: int,
        applicant_type: str | None = None,
    ) -> list[CreditProductRequirement]:
        normalized_type = (applicant_type or "ALL").strip().upper()
        statement = (
            select(CreditProductRequirement)
            .where(
                CreditProductRequirement.product_id == product_id,
                or_(
                    CreditProductRequirement.applicant_type == "ALL",
                    CreditProductRequirement.applicant_type == normalized_type,
                ),
            )
            .order_by(CreditProductRequirement.display_order)
        )
        return list(self.db.scalars(statement))

    def get_active_policy(self, as_of: date | None = None) -> CreditPolicyVersion | None:
        effective_date = as_of or date.today()
        return self.db.scalar(
            select(CreditPolicyVersion)
            .where(
                CreditPolicyVersion.status == "ACTIVE",
                CreditPolicyVersion.effective_from <= effective_date,
                or_(
                    CreditPolicyVersion.effective_to.is_(None),
                    CreditPolicyVersion.effective_to >= effective_date,
                ),
            )
            .order_by(CreditPolicyVersion.effective_from.desc())
        )

    def list_active_rules(
        self,
        policy_version_id: int,
        product_id: int,
    ) -> list[CreditPolicyRule]:
        return list(
            self.db.scalars(
                select(CreditPolicyRule)
                .where(
                    CreditPolicyRule.policy_version_id == policy_version_id,
                    CreditPolicyRule.product_id == product_id,
                    CreditPolicyRule.is_active.is_(True),
                )
                .order_by(CreditPolicyRule.display_order)
            )
        )
