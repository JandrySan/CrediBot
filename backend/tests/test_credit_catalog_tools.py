from datetime import date
from decimal import Decimal

from app.database.session import SessionLocal
from app.models.credit_policy import CreditPolicyRule, CreditPolicyVersion
from app.models.credit_product import CreditProduct, CreditProductRequirement
from app.repositories.credit_catalog_repository import CreditCatalogRepository
from app.services.tools.policy_tools import (
    consultar_requisitos_producto,
    listar_productos_credito,
    obtener_reglas_credito,
)


def _seed_catalog(db) -> CreditProduct:
    product = CreditProduct(
        code="CONSUMO_PERSONAL_DEMO",
        name="Consumo de prueba",
        segment="CONSUMPTION",
        description="Producto creado para probar el catalogo.",
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
    db.flush()
    db.add_all(
        [
            CreditProductRequirement(
                product_id=product.id,
                code="NATIONAL_ID",
                name="Cedula",
                description="Identidad",
                applicant_type="ALL",
                requirement_type="DOCUMENT",
                stage="APPLICATION",
                display_order=1,
            ),
            CreditProductRequirement(
                product_id=product.id,
                code="PAYSLIP",
                name="Rol de pagos",
                description="Ingresos dependientes",
                applicant_type="EMPLOYED",
                requirement_type="DOCUMENT",
                stage="APPLICATION",
                display_order=2,
            ),
        ]
    )
    policy = CreditPolicyVersion(
        code="DEMO_EC_TEST",
        name="Politica de prueba",
        status="ACTIVE",
        description="Politica para pruebas.",
        is_demo=True,
        effective_from=date(2026, 1, 1),
    )
    db.add(policy)
    db.flush()
    db.add(
        CreditPolicyRule(
            policy_version_id=policy.id,
            product_id=product.id,
            code="MAXIMUM_PROJECTED_DTI",
            category="CAPACITY",
            parameters={"maximum": 0.4},
            severity="BLOCKING",
            outcome_on_failure="NOT_PREQUALIFIED",
            explanation="Limite de carga.",
            display_order=1,
        )
    )
    db.flush()
    return product


def test_catalog_tools_read_products_requirements_and_rules_from_database():
    with SessionLocal.begin() as db:
        product = _seed_catalog(db)
        repository = CreditCatalogRepository(db)

        assert repository.resolve_product("consumo").id == product.id

        product_result = listar_productos_credito(db=db)
        assert product_result["productos"][0]["tasa_efectiva_anual"] == 15.5

        requirement_result = consultar_requisitos_producto(
            producto="consumo",
            tipo_solicitante="EMPLOYED",
            db=db,
        )
        assert [item["codigo"] for item in requirement_result["requisitos"]] == [
            "NATIONAL_ID",
            "PAYSLIP",
        ]

        rules_result = obtener_reglas_credito(producto="consumo", db=db)
        assert rules_result["politica"]["codigo"] == "DEMO_EC_TEST"
        assert rules_result["reglas"] == [
            {
                "codigo": "MAXIMUM_PROJECTED_DTI",
                "categoria": "CAPACITY",
                "parametros": {"maximum": 0.4},
                "resultado_si_incumple": "NOT_PREQUALIFIED",
                "explicacion": "Limite de carga.",
            }
        ]
