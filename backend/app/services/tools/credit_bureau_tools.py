from sqlalchemy.orm import Session

from app.services.credit_bureau.profile_service import (
    CreditBureauProfileService,
    CreditBureauUnavailable,
)
from app.services.tools.tool_registry import tool


@tool(
    name="consultar_historial_crediticio",
    description=(
        "Consulta la central de riesgo simulada de una persona por cedula o telefono. "
        "Devuelve identidad, score, riesgo, deuda, mora, pagos fallidos, eventos negativos, "
        "consultas recientes, capacidad estimada y resultado preliminar."
    ),
    parameters={
        "type": "object",
        "properties": {
            "identificador": {
                "type": "string",
                "description": "Cedula de 10 digitos o telefono con codigo de pais.",
            },
        },
        "required": ["identificador"],
    },
    requires_db=True,
)
def consultar_historial_crediticio(identificador: str, db: Session) -> dict:
    try:
        profile = CreditBureauProfileService(db).find_profile(identificador)
    except CreditBureauUnavailable:
        return {
            "encontrado": False,
            "mensaje": "El historial crediticio no esta disponible en este momento.",
        }

    if not profile:
        return {
            "encontrado": False,
            "mensaje": "No se encontro historial crediticio para ese identificador.",
        }

    return profile
