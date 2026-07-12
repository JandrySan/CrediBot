from app.services.tools.tool_registry import tool


@tool(
    name="calcular_amortizacion",
    description=(
        "Calcula la tabla de amortizacion mensual para un credito. "
        "Devuelve cuota mensual, total de intereses, total a pagar y el detalle mes a mes."
    ),
    parameters={
        "type": "object",
        "properties": {
            "monto": {
                "type": "number",
                "description": "Monto total del prestamo en dolares",
            },
            "plazo_meses": {
                "type": "integer",
                "description": "Plazo en meses para pagar el credito",
            },
            "tasa_interes_anual": {
                "type": "number",
                "description": "Tasa de interes anual en porcentaje (ej: 15 para 15%%)",
            },
        },
        "required": ["monto", "plazo_meses", "tasa_interes_anual"],
    },
)
def calcular_amortizacion(
    monto: float,
    plazo_meses: int,
    tasa_interes_anual: float,
) -> dict:
    if monto <= 0:
        return {"error": "El monto debe ser mayor a cero"}

    if plazo_meses <= 0:
        return {"error": "El plazo debe ser mayor a cero"}

    if tasa_interes_anual < 0:
        return {"error": "La tasa de interes no puede ser negativa"}

    tasa_mensual = (tasa_interes_anual / 100) / 12

    if tasa_mensual == 0:
        cuota_mensual = monto / plazo_meses
    else:
        cuota_mensual = monto * (
            tasa_mensual * (1 + tasa_mensual) ** plazo_meses
        ) / (
            (1 + tasa_mensual) ** plazo_meses - 1
        )

    saldo = monto
    total_intereses = 0.0
    detalle = []

    for mes in range(1, plazo_meses + 1):
        interes_mes = saldo * tasa_mensual
        capital_mes = cuota_mensual - interes_mes
        saldo -= capital_mes
        total_intereses += interes_mes

        detalle.append({
            "mes": mes,
            "cuota": round(cuota_mensual, 2),
            "interes": round(interes_mes, 2),
            "capital": round(capital_mes, 2),
            "saldo": round(abs(saldo), 2),
        })

    total_pagar = monto + total_intereses

    return {
        "monto_solicitado": round(monto, 2),
        "plazo_meses": plazo_meses,
        "tasa_interes_anual": tasa_interes_anual,
        "cuota_mensual": round(cuota_mensual, 2),
        "total_intereses": round(total_intereses, 2),
        "total_pagar": round(total_pagar, 2),
        "detalle_mensual": detalle,
    }
