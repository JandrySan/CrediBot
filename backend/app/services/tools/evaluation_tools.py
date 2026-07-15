from decimal import Decimal

from sqlalchemy.orm import Session

from app.repositories.credit_catalog_repository import CreditCatalogRepository
from app.services.rules.versioned_credit_rule_engine import (
    CreditEvaluationInput,
    VersionedCreditRuleEngine,
)
from app.services.tools.tool_registry import tool


@tool(
    name="evaluar_precalificacion",
    description=(
        "Ejecuta una precalificacion informativa con la tasa y las reglas vigentes de la base. "
        "No consulta el buro ni produce una aprobacion final."
    ),
    parameters={
        "type": "object",
        "properties": {
            "producto": {"type": "string"},
            "monto": {"type": "number"},
            "plazo_meses": {"type": "integer"},
            "ingreso_mensual": {"type": "number"},
            "otros_ingresos": {"type": "number"},
            "gastos_mensuales": {"type": "number"},
            "cuotas_deuda_actuales": {"type": "number"},
            "edad": {"type": "integer"},
            "situacion_laboral": {"type": "string"},
            "antiguedad_laboral_meses": {"type": "integer"},
            "antiguedad_negocio_meses": {"type": "integer"},
        },
        "required": ["producto", "monto", "plazo_meses", "ingreso_mensual"],
    },
    requires_db=True,
)
def evaluar_precalificacion(
    producto: str,
    monto: float,
    plazo_meses: int,
    ingreso_mensual: float,
    db: Session,
    otros_ingresos: float = 0,
    gastos_mensuales: float | None = None,
    cuotas_deuda_actuales: float = 0,
    edad: int | None = None,
    situacion_laboral: str | None = None,
    antiguedad_laboral_meses: int | None = None,
    antiguedad_negocio_meses: int | None = None,
) -> dict:
    repository = CreditCatalogRepository(db)
    resolved = repository.resolve_product(producto)
    policy = repository.get_active_policy()
    if resolved is None or policy is None:
        return {
            "resultado": "ERROR",
            "mensaje": "No existe un producto o una politica vigente para evaluar.",
        }

    rules = repository.list_active_rules(policy.id, resolved.id)
    evaluation = VersionedCreditRuleEngine().evaluate(
        product=resolved,
        policy=policy,
        rules=rules,
        data=CreditEvaluationInput(
            amount=Decimal(str(monto)),
            term_months=plazo_meses,
            monthly_net_income=Decimal(str(ingreso_mensual)),
            other_monthly_income=Decimal(str(otros_ingresos)),
            monthly_living_expenses=(
                None if gastos_mensuales is None else Decimal(str(gastos_mensuales))
            ),
            existing_monthly_debt_payments=Decimal(str(cuotas_deuda_actuales)),
            age=edad,
            employment_status=situacion_laboral,
            job_tenure_months=antiguedad_laboral_meses,
            business_tenure_months=antiguedad_negocio_meses,
        ),
    )
    result = evaluation.to_dict()
    result["nota"] = (
        "Es una simulacion sin consulta de buro ni verificacion documental; no es una "
        "aprobacion final."
    )
    return result
