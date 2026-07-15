from sqlalchemy.orm import Session

from app.models.credit_application import CreditApplication
from app.models.customer import Customer
from app.services.tools.tool_registry import tool


@tool(
    name="consultar_estado_cliente",
    description=(
        "Consulta el estado actual de un cliente por su numero de telefono. "
        "Devuelve su informacion basica, solicitudes de credito previas y sus resultados."
    ),
    parameters={
        "type": "object",
        "properties": {
            "telefono": {
                "type": "string",
                "description": "Numero de telefono del cliente (incluyendo codigo de pais, ej: +51999123456)",
            },
        },
        "required": ["telefono"],
    },
    requires_db=True,
)
def consultar_estado_cliente(telefono: str, db: Session) -> dict:
    customer = db.query(Customer).filter(Customer.phone_number == telefono).first()

    if not customer:
        return {
            "encontrado": False,
            "mensaje": "No se encontro un cliente con ese numero de telefono",
        }

    applications = (
        db.query(CreditApplication)
        .filter(CreditApplication.customer_id == customer.id)
        .order_by(CreditApplication.id.desc())
        .all()
    )

    solicitudes = []
    for app in applications:
        solicitudes.append(
            {
                "id": app.id,
                "monto": float(app.amount) if app.amount else None,
                "plazo_meses": app.term_months,
                "ingreso_mensual": float(app.monthly_income) if app.monthly_income else None,
                "resultado": app.result,
                "motivo": app.reason,
                "fecha": str(app.created_at) if app.created_at else None,
            }
        )

    return {
        "encontrado": True,
        "cliente": {
            "id": customer.id,
            "nombre": customer.full_name,
            "telefono": customer.phone_number,
            "fecha_registro": str(customer.created_at) if customer.created_at else None,
        },
        "solicitudes": solicitudes,
        "total_solicitudes": len(solicitudes),
    }
