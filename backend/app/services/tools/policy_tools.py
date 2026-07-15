from decimal import Decimal

from sqlalchemy.orm import Session

from app.repositories.credit_catalog_repository import CreditCatalogRepository
from app.services.tools.tool_registry import tool


@tool(
    name="listar_productos_credito",
    description=(
        "Lista los productos de credito vigentes disponibles para una simulacion o "
        "precalificacion, con montos, plazos y tasas provenientes de la base de datos."
    ),
    parameters={"type": "object", "properties": {}, "required": []},
    requires_db=True,
)
def listar_productos_credito(db: Session) -> dict:
    products = CreditCatalogRepository(db).list_active_products()
    return {
        "productos": [_serialize_product(product) for product in products],
        "total": len(products),
        "nota": ("Los productos marcados como demo son informativos y no constituyen una oferta."),
    }


@tool(
    name="consultar_requisitos_producto",
    description=(
        "Consulta en la base los documentos, datos y autorizaciones requeridos para un "
        "producto y tipo de solicitante."
    ),
    parameters={
        "type": "object",
        "properties": {
            "producto": {
                "type": "string",
                "description": "Codigo o nombre del producto, por ejemplo consumo o microcredito.",
            },
            "tipo_solicitante": {
                "type": "string",
                "enum": ["ALL", "EMPLOYED", "SELF_EMPLOYED", "RETIRED", "RENTIER"],
                "description": "Fuente principal de ingresos del solicitante.",
            },
        },
        "required": ["producto"],
    },
    requires_db=True,
)
def consultar_requisitos_producto(
    producto: str,
    db: Session,
    tipo_solicitante: str = "ALL",
) -> dict:
    repository = CreditCatalogRepository(db)
    resolved = repository.resolve_product(producto)
    if resolved is None:
        return {
            "encontrado": False,
            "mensaje": "No encontre un producto vigente con ese nombre.",
        }

    requirements = repository.list_requirements(resolved.id, tipo_solicitante)
    return {
        "encontrado": True,
        "producto": _serialize_product(resolved),
        "tipo_solicitante": tipo_solicitante.upper(),
        "requisitos": [
            {
                "codigo": requirement.code,
                "nombre": requirement.name,
                "descripcion": requirement.description,
                "tipo": requirement.requirement_type,
                "etapa": requirement.stage,
                "obligatorio": requirement.is_required,
            }
            for requirement in requirements
        ],
        "nota": "La lista es demostrativa y puede requerir validacion de un asesor.",
    }


@tool(
    name="obtener_reglas_credito",
    description=(
        "Obtiene las reglas versionadas que usa la precalificacion de un producto para "
        "explicar sus criterios sin inventar umbrales."
    ),
    parameters={
        "type": "object",
        "properties": {
            "producto": {
                "type": "string",
                "description": "Codigo o nombre del producto; si se omite se usa consumo.",
            }
        },
        "required": [],
    },
    requires_db=True,
)
def obtener_reglas_credito(db: Session, producto: str = "consumo") -> dict:
    repository = CreditCatalogRepository(db)
    resolved = repository.resolve_product(producto)
    policy = repository.get_active_policy()
    if resolved is None or policy is None:
        return {
            "encontrado": False,
            "mensaje": "No existe una politica activa para ese producto.",
        }

    rules = repository.list_active_rules(policy.id, resolved.id)
    return {
        "encontrado": True,
        "producto": resolved.code,
        "politica": {
            "codigo": policy.code,
            "nombre": policy.name,
            "es_demo": policy.is_demo,
            "vigente_desde": policy.effective_from.isoformat(),
        },
        "reglas": [
            {
                "codigo": rule.code,
                "categoria": rule.category,
                "parametros": rule.parameters,
                "resultado_si_incumple": rule.outcome_on_failure,
                "explicacion": rule.explanation,
            }
            for rule in rules
        ],
        "nota": "La precalificacion es informativa y admite revision humana.",
    }


@tool(
    name="consultar_politica",
    description=(
        "Responde desde la base consultas sobre productos, requisitos, tasas, montos, "
        "plazos o criterios de precalificacion."
    ),
    parameters={
        "type": "object",
        "properties": {
            "consulta": {
                "type": "string",
                "description": "Pregunta o tema sobre el credito.",
            },
            "producto": {
                "type": "string",
                "description": "Producto de interes, si el usuario lo indico.",
            },
        },
        "required": ["consulta"],
    },
    requires_db=True,
)
def consultar_politica(
    consulta: str,
    db: Session,
    producto: str = "consumo",
) -> dict:
    normalized = (consulta or "").lower()
    if any(word in normalized for word in ("requisito", "documento", "papel", "necesito")):
        return consultar_requisitos_producto(producto=producto, db=db)
    if any(word in normalized for word in ("regla", "criterio", "rechazo", "aprobado")):
        return obtener_reglas_credito(producto=producto, db=db)

    repository = CreditCatalogRepository(db)
    resolved = repository.resolve_product(producto)
    if resolved is None:
        return {
            "encontrado": False,
            "mensaje": "No encontre un producto vigente para responder esa consulta.",
        }

    return {
        "encontrado": True,
        "producto": _serialize_product(resolved),
        "respuesta_base": _product_answer(normalized, resolved),
        "nota": (
            "Las condiciones son demostrativas, no garantizan aprobacion y deben confirmarse "
            "antes de contratar."
        ),
    }


def _serialize_product(product) -> dict:
    return {
        "codigo": product.code,
        "nombre": product.name,
        "segmento": product.segment,
        "descripcion": product.description,
        "moneda": product.currency,
        "monto_minimo": _number(product.min_amount),
        "monto_maximo": _number(product.max_amount),
        "plazo_minimo_meses": product.min_term_months,
        "plazo_maximo_meses": product.max_term_months,
        "tasa_efectiva_anual": _number(product.effective_annual_rate),
        "tasa_maxima_segmento": _number(product.max_effective_annual_rate),
        "amortizacion": product.amortization_type,
        "es_demo": product.is_demo,
        "vigente_desde": product.effective_from.isoformat(),
        "fuente": product.source_url,
    }


def _product_answer(consulta: str, product) -> str:
    if any(word in consulta for word in ("tasa", "interes", "interés")):
        return (
            f"La tasa efectiva anual demostrativa es {_number(product.effective_annual_rate)}% "
            f"y el maximo registrado para el segmento es "
            f"{_number(product.max_effective_annual_rate)}%."
        )
    if any(word in consulta for word in ("monto", "cuanto", "cuánto")):
        return (
            f"El rango demostrativo va de USD {_number(product.min_amount)} a "
            f"USD {_number(product.max_amount)}."
        )
    if any(word in consulta for word in ("plazo", "mes", "tiempo")):
        return (
            f"El plazo demostrativo va de {product.min_term_months} a "
            f"{product.max_term_months} meses."
        )
    return product.description


def _number(value: Decimal) -> int | float:
    if value == value.to_integral_value():
        return int(value)
    return float(value)
