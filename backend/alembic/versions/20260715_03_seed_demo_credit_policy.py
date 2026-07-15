"""Carga productos, requisitos y politica demostrativa versionada."""

import json
from datetime import date

from alembic import op
import sqlalchemy as sa


revision = "20260715_03"
down_revision = "20260715_02"
branch_labels = None
depends_on = None


PRODUCTS = (
    {
        "code": "CONSUMO_PERSONAL_DEMO",
        "name": "Crédito de consumo personal (demo)",
        "segment": "CONSUMPTION",
        "description": (
            "Préstamo demostrativo para gastos personales no relacionados con una "
            "actividad productiva. La precalificación es informativa."
        ),
        "currency": "USD",
        "min_amount": 500,
        "max_amount": 30000,
        "min_term_months": 6,
        "max_term_months": 60,
        "effective_annual_rate": 15.50,
        "max_effective_annual_rate": 16.77,
        "amortization_type": "FRENCH",
        "payment_frequency": "MONTHLY",
        "is_active": True,
        "is_demo": True,
        "source_url": (
            "https://contenido.bce.fin.ec/documentos/Estadisticas/"
            "SectorMonFin/TasasInteres/Indice.htm"
        ),
        "effective_from": date(2026, 7, 1),
    },
    {
        "code": "MICROCREDITO_MINORISTA_DEMO",
        "name": "Microcrédito minorista (demo)",
        "segment": "MICROCREDIT_RETAIL",
        "description": (
            "Financiamiento demostrativo para una actividad productiva de pequeña escala, "
            "sujeto a verificación del negocio y su flujo."
        ),
        "currency": "USD",
        "min_amount": 500,
        "max_amount": 20000,
        "min_term_months": 6,
        "max_term_months": 48,
        "effective_annual_rate": 24.00,
        "max_effective_annual_rate": 28.23,
        "amortization_type": "FRENCH",
        "payment_frequency": "MONTHLY",
        "is_active": True,
        "is_demo": True,
        "source_url": (
            "https://contenido.bce.fin.ec/documentos/Estadisticas/"
            "SectorMonFin/TasasInteres/Indice.htm"
        ),
        "effective_from": date(2026, 7, 1),
    },
)


COMMON_REQUIREMENTS = (
    ("NATIONAL_ID", "Cédula de identidad", "DOCUMENT", "ALL", 10),
    ("PRIVACY_NOTICE", "Aviso de privacidad informado", "CONSENT", "ALL", 20),
    ("BUREAU_AUTHORIZATION", "Autorización de consulta crediticia", "CONSENT", "ALL", 30),
    ("ADDRESS_EVIDENCE", "Planilla de servicio o evidencia de domicilio", "DOCUMENT", "ALL", 40),
    ("MONTHLY_INCOME", "Ingresos mensuales", "DATA", "ALL", 50),
    ("MONTHLY_EXPENSES", "Gastos mensuales del hogar", "DATA", "ALL", 60),
    ("CURRENT_DEBTS", "Cuotas de deudas vigentes", "DATA", "ALL", 70),
    ("PAYSLIP", "Rol de pagos reciente", "DOCUMENT", "EMPLOYED", 80),
    ("EMPLOYMENT_CERTIFICATE", "Certificado laboral o historia IESS", "DOCUMENT", "EMPLOYED", 90),
    ("RUC", "Registro Único de Contribuyentes", "DOCUMENT", "SELF_EMPLOYED", 100),
    ("TAX_RETURNS", "Declaraciones tributarias", "DOCUMENT", "SELF_EMPLOYED", 110),
    ("BANK_STATEMENTS", "Estados de cuenta", "DOCUMENT", "SELF_EMPLOYED", 120),
    ("PENSION_EVIDENCE", "Comprobante de pensión", "DOCUMENT", "RETIRED", 130),
    ("RENT_CONTRACT", "Contrato de arrendamiento", "DOCUMENT", "RENTIER", 140),
)


CONSUMPTION_RULES = (
    ("AMOUNT_IN_RANGE", "APPLICATION", {"use_product_range": True}, "NOT_PREQUALIFIED", 10),
    ("TERM_IN_RANGE", "APPLICATION", {"use_product_range": True}, "NOT_PREQUALIFIED", 20),
    ("MINIMUM_AGE", "IDENTITY", {"minimum_age": 21}, "NOT_PREQUALIFIED", 30),
    (
        "MAXIMUM_AGE_AT_MATURITY",
        "IDENTITY",
        {"maximum_age": 70},
        "MANUAL_REVIEW",
        40,
    ),
    ("IDENTITY_VERIFIED", "KYC", {"required": True}, "NEEDS_INFORMATION", 50),
    ("PEP_REVIEW", "KYC", {"manual_review_if_pep": True}, "MANUAL_REVIEW", 60),
    ("MINIMUM_MONTHLY_INCOME", "CAPACITY", {"minimum": 600}, "NOT_PREQUALIFIED", 70),
    ("EXPENSES_DECLARED", "CAPACITY", {"required": True}, "NEEDS_INFORMATION", 80),
    ("MAXIMUM_PROJECTED_DTI", "CAPACITY", {"maximum": 0.40}, "NOT_PREQUALIFIED", 90),
    (
        "MINIMUM_DISPOSABLE_AFTER_PAYMENT",
        "CAPACITY",
        {"minimum": 100},
        "NOT_PREQUALIFIED",
        100,
    ),
    (
        "MINIMUM_EMPLOYMENT_TENURE",
        "STABILITY",
        {"months": 6, "employment_status": "EMPLOYED"},
        "MANUAL_REVIEW",
        110,
    ),
    ("MINIMUM_CREDIT_SCORE", "HISTORY", {"minimum": 560}, "MANUAL_REVIEW", 120),
    (
        "NO_ACTIVE_SEVERE_DELINQUENCY",
        "HISTORY",
        {"maximum_days_past_due": 60},
        "NOT_PREQUALIFIED",
        130,
    ),
    ("MAXIMUM_RECENT_INQUIRIES", "HISTORY", {"maximum_6m": 6}, "MANUAL_REVIEW", 140),
)


MICROCREDIT_RULES = (
    ("AMOUNT_IN_RANGE", "APPLICATION", {"use_product_range": True}, "NOT_PREQUALIFIED", 10),
    ("TERM_IN_RANGE", "APPLICATION", {"use_product_range": True}, "NOT_PREQUALIFIED", 20),
    ("MINIMUM_AGE", "IDENTITY", {"minimum_age": 21}, "NOT_PREQUALIFIED", 30),
    (
        "MAXIMUM_AGE_AT_MATURITY",
        "IDENTITY",
        {"maximum_age": 70},
        "MANUAL_REVIEW",
        40,
    ),
    ("IDENTITY_VERIFIED", "KYC", {"required": True}, "NEEDS_INFORMATION", 50),
    ("PEP_REVIEW", "KYC", {"manual_review_if_pep": True}, "MANUAL_REVIEW", 60),
    ("MINIMUM_MONTHLY_INCOME", "CAPACITY", {"minimum": 500}, "NOT_PREQUALIFIED", 70),
    ("EXPENSES_DECLARED", "CAPACITY", {"required": True}, "NEEDS_INFORMATION", 80),
    ("MAXIMUM_PROJECTED_DTI", "CAPACITY", {"maximum": 0.45}, "NOT_PREQUALIFIED", 90),
    (
        "MINIMUM_DISPOSABLE_AFTER_PAYMENT",
        "CAPACITY",
        {"minimum": 75},
        "NOT_PREQUALIFIED",
        100,
    ),
    (
        "MINIMUM_BUSINESS_TENURE",
        "STABILITY",
        {"months": 12, "employment_status": "SELF_EMPLOYED"},
        "MANUAL_REVIEW",
        110,
    ),
    ("MINIMUM_CREDIT_SCORE", "HISTORY", {"minimum": 520}, "MANUAL_REVIEW", 120),
    (
        "NO_ACTIVE_SEVERE_DELINQUENCY",
        "HISTORY",
        {"maximum_days_past_due": 60},
        "NOT_PREQUALIFIED",
        130,
    ),
    ("MAXIMUM_RECENT_INQUIRIES", "HISTORY", {"maximum_6m": 7}, "MANUAL_REVIEW", 140),
)


EXPLANATIONS = {
    "AMOUNT_IN_RANGE": "El monto debe estar dentro del rango vigente del producto.",
    "TERM_IN_RANGE": "El plazo debe estar dentro del rango vigente del producto.",
    "MINIMUM_AGE": "La edad mínima es una condición demostrativa del producto.",
    "MAXIMUM_AGE_AT_MATURITY": "La edad al vencimiento requiere una revisión adicional.",
    "IDENTITY_VERIFIED": "La identidad debe verificarse antes de una decisión formal.",
    "PEP_REVIEW": "Una condición PEP requiere debida diligencia y revisión humana.",
    "MINIMUM_MONTHLY_INCOME": "El ingreso verificable debe cubrir el mínimo de la política.",
    "EXPENSES_DECLARED": "Los gastos son necesarios para no sobreestimar la capacidad de pago.",
    "MAXIMUM_PROJECTED_DTI": "La carga total proyectada no debe superar el límite del producto.",
    "MINIMUM_DISPOSABLE_AFTER_PAYMENT": "Debe quedar un ingreso disponible mínimo tras la cuota.",
    "MINIMUM_EMPLOYMENT_TENURE": "La estabilidad laboral requiere una revisión adicional.",
    "MINIMUM_BUSINESS_TENURE": "La antigüedad del negocio requiere una revisión adicional.",
    "MINIMUM_CREDIT_SCORE": "El puntaje se usa como señal y puede requerir revisión humana.",
    "NO_ACTIVE_SEVERE_DELINQUENCY": "Una mora severa activa incumple la política demostrativa.",
    "MAXIMUM_RECENT_INQUIRIES": "Muchas consultas recientes requieren revisión adicional.",
}


def upgrade() -> None:
    bind = op.get_bind()
    product_ids = {product["code"]: _upsert_product(bind, product) for product in PRODUCTS}
    policy_id = _upsert_policy(bind)

    for product_code, product_id in product_ids.items():
        _insert_requirements(bind, product_id, product_code)
        rules = CONSUMPTION_RULES if product_code == "CONSUMO_PERSONAL_DEMO" else MICROCREDIT_RULES
        _insert_rules(bind, policy_id, product_id, rules)


def downgrade() -> None:
    bind = op.get_bind()
    policy_id = bind.execute(
        sa.text("SELECT id FROM credit_policy_versions WHERE code = :code"),
        {"code": "DEMO_EC_2026_01"},
    ).scalar_one_or_none()
    if policy_id is not None:
        bind.execute(
            sa.text("DELETE FROM credit_policy_rules WHERE policy_version_id = :policy_id"),
            {"policy_id": policy_id},
        )
        bind.execute(
            sa.text("DELETE FROM credit_policy_versions WHERE id = :policy_id"),
            {"policy_id": policy_id},
        )

    for product in PRODUCTS:
        product_id = bind.execute(
            sa.text("SELECT id FROM credit_products WHERE code = :code"),
            {"code": product["code"]},
        ).scalar_one_or_none()
        if product_id is not None:
            bind.execute(
                sa.text("DELETE FROM credit_product_requirements WHERE product_id = :product_id"),
                {"product_id": product_id},
            )
            bind.execute(
                sa.text("DELETE FROM credit_products WHERE id = :product_id"),
                {"product_id": product_id},
            )


def _upsert_product(bind, product: dict) -> int:
    product_id = bind.execute(
        sa.text("SELECT id FROM credit_products WHERE code = :code"),
        {"code": product["code"]},
    ).scalar_one_or_none()
    if product_id is None:
        result = bind.execute(
            sa.text(
                """
                INSERT INTO credit_products (
                    code, name, segment, description, currency, min_amount, max_amount,
                    min_term_months, max_term_months, effective_annual_rate,
                    max_effective_annual_rate, amortization_type, payment_frequency,
                    is_active, is_demo, source_url, effective_from
                ) VALUES (
                    :code, :name, :segment, :description, :currency, :min_amount,
                    :max_amount, :min_term_months, :max_term_months,
                    :effective_annual_rate, :max_effective_annual_rate,
                    :amortization_type, :payment_frequency, :is_active, :is_demo,
                    :source_url, :effective_from
                )
                RETURNING id
                """
            ),
            product,
        )
        return int(result.scalar_one())

    bind.execute(
        sa.text(
            """
            UPDATE credit_products SET
                name = :name,
                segment = :segment,
                description = :description,
                currency = :currency,
                min_amount = :min_amount,
                max_amount = :max_amount,
                min_term_months = :min_term_months,
                max_term_months = :max_term_months,
                effective_annual_rate = :effective_annual_rate,
                max_effective_annual_rate = :max_effective_annual_rate,
                amortization_type = :amortization_type,
                payment_frequency = :payment_frequency,
                is_active = :is_active,
                is_demo = :is_demo,
                source_url = :source_url,
                effective_from = :effective_from
            WHERE code = :code
            """
        ),
        product,
    )
    return int(product_id)


def _upsert_policy(bind) -> int:
    parameters = {
        "code": "DEMO_EC_2026_01",
        "name": "Política demostrativa Ecuador 2026.01",
        "status": "ACTIVE",
        "description": (
            "Reglas sintéticas para pruebas funcionales. No constituyen una política bancaria "
            "aprobada ni una oferta de crédito."
        ),
        "is_demo": True,
        "effective_from": date(2026, 7, 1),
    }
    policy_id = bind.execute(
        sa.text("SELECT id FROM credit_policy_versions WHERE code = :code"), parameters
    ).scalar_one_or_none()
    if policy_id is not None:
        bind.execute(
            sa.text(
                """
                UPDATE credit_policy_versions SET
                    name = :name, status = :status, description = :description,
                    is_demo = :is_demo, effective_from = :effective_from
                WHERE code = :code
                """
            ),
            parameters,
        )
        return int(policy_id)

    return int(
        bind.execute(
            sa.text(
                """
                INSERT INTO credit_policy_versions (
                    code, name, status, description, is_demo, effective_from
                ) VALUES (
                    :code, :name, :status, :description, :is_demo, :effective_from
                ) RETURNING id
                """
            ),
            parameters,
        ).scalar_one()
    )


def _insert_requirements(bind, product_id: int, product_code: str) -> None:
    existing = set(
        bind.execute(
            sa.text("SELECT code FROM credit_product_requirements WHERE product_id = :product_id"),
            {"product_id": product_id},
        ).scalars()
    )
    requirements = list(COMMON_REQUIREMENTS)
    if product_code == "MICROCREDITO_MINORISTA_DEMO":
        requirements.extend(
            (
                ("BUSINESS_TENURE", "Antigüedad del negocio", "DATA", "SELF_EMPLOYED", 150),
                (
                    "CASH_FLOW",
                    "Flujo de ingresos y gastos del negocio",
                    "DOCUMENT",
                    "SELF_EMPLOYED",
                    160,
                ),
                ("CREDIT_PURPOSE", "Destino productivo del crédito", "DATA", "ALL", 170),
            )
        )

    for code, name, requirement_type, applicant_type, order in requirements:
        if code in existing:
            continue
        bind.execute(
            sa.text(
                """
                INSERT INTO credit_product_requirements (
                    product_id, code, name, description, applicant_type,
                    requirement_type, stage, is_required, conditions, display_order
                ) VALUES (
                    :product_id, :code, :name, :description, :applicant_type,
                    :requirement_type, 'APPLICATION', true, '{}', :display_order
                )
                """
            ),
            {
                "product_id": product_id,
                "code": code,
                "name": name,
                "description": f"Requisito demostrativo: {name.lower()}.",
                "applicant_type": applicant_type,
                "requirement_type": requirement_type,
                "display_order": order,
            },
        )


def _insert_rules(bind, policy_id: int, product_id: int, rules: tuple) -> None:
    existing = set(
        bind.execute(
            sa.text(
                """
                SELECT code FROM credit_policy_rules
                WHERE policy_version_id = :policy_id AND product_id = :product_id
                """
            ),
            {"policy_id": policy_id, "product_id": product_id},
        ).scalars()
    )
    for code, category, parameters, outcome, order in rules:
        if code in existing:
            continue
        bind.execute(
            sa.text(
                """
                INSERT INTO credit_policy_rules (
                    policy_version_id, product_id, code, category, parameters,
                    severity, outcome_on_failure, explanation, display_order, is_active
                ) VALUES (
                    :policy_id, :product_id, :code, :category, :parameters,
                    :severity, :outcome, :explanation, :display_order, true
                )
                """
            ),
            {
                "policy_id": policy_id,
                "product_id": product_id,
                "code": code,
                "category": category,
                "parameters": json.dumps(parameters, ensure_ascii=False),
                "severity": "REVIEW" if outcome == "MANUAL_REVIEW" else "BLOCKING",
                "outcome": outcome,
                "explanation": EXPLANATIONS[code],
                "display_order": order,
            },
        )
