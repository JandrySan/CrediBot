from app.services.tools.tool_registry import tool


@tool(
    name="obtener_reglas_credito",
    description=(
        "Obtiene las reglas de negocio actuales del motor de precalificacion de credito. "
        "Sirve para explicar al cliente por que fue aprobado u observado."
    ),
    parameters={
        "type": "object",
        "properties": {},
        "required": [],
    },
)
def obtener_reglas_credito() -> dict:
    return {
        "reglas": [
            {
                "campo": "ingreso_mensual",
                "condicion": "menor a 600 USD",
                "resultado": "OBSERVADO",
                "descripcion": "El ingreso mensual debe ser mayor o igual a 600 USD",
            },
            {
                "campo": "monto_vs_ingreso",
                "condicion": "monto solicitado mayor a ingreso mensual * 8",
                "resultado": "OBSERVADO",
                "descripcion": "El monto solicitado no debe exceder 8 veces el ingreso mensual",
            },
            {
                "campo": "plazo",
                "condicion": "mayor a 60 meses",
                "resultado": "OBSERVADO",
                "descripcion": "El plazo maximo permitido es de 60 meses",
            },
            {
                "campo": "todas_las_reglas",
                "condicion": "ninguna regla observada",
                "resultado": "PREAPROBADO",
                "descripcion": "Si cumple todas las reglas, el resultado es preaprobado",
            },
        ],
        "nota": "Estas reglas son orientativas. La decision final la toma un asesor humano.",
    }


@tool(
    name="consultar_politica",
    description=(
        "Busca informacion sobre politicas, terminos y condiciones, o preguntas frecuentes "
        "relacionadas con creditos. Responde dudas sobre requisitos, documentos, plazos, etc."
    ),
    parameters={
        "type": "object",
        "properties": {
            "consulta": {
                "type": "string",
                "description": "La pregunta o tema que el cliente quiere consultar",
            },
        },
        "required": ["consulta"],
    },
)
def consultar_politica(consulta: str) -> dict:
    consulta_lower = consulta.lower()
    resultados: list[dict[str, str | int]] = []

    faqs = [
        {
            "pregunta": "¿Cuales son los requisitos para solicitar un credito?",
            "respuesta": "Los requisitos basicos son: ser mayor de edad, tener ingresos mensuales minimos de 600 USD, presentar documento de identidad vigente y comprobante de ingresos.",
            "palabras_clave": ["requisitos", "necesito", "documentos", "papeles", "pedir"],
        },
        {
            "pregunta": "¿Cual es el monto maximo que puedo solicitar?",
            "respuesta": "El monto maximo depende de tus ingresos mensuales. Como regla general, no puede superar 8 veces tu ingreso mensual.",
            "palabras_clave": ["monto", "maximo", "limite", "cuanto", "prestamo"],
        },
        {
            "pregunta": "¿Cual es el plazo maximo para pagar?",
            "respuesta": "El plazo maximo es de 60 meses (5 anos). El plazo minimo es de 6 meses.",
            "palabras_clave": ["plazo", "meses", "anos", "tiempo", "pagar", "cuotas"],
        },
        {
            "pregunta": "¿Que tasa de interes manejan?",
            "respuesta": "Las tasas de interes varian segun el perfil del cliente y el monto solicitado. Un asesor humano te dara la tasa exacta aplicable a tu caso.",
            "palabras_clave": ["interes", "tasa", "intereses", "porcentaje", "tea"],
        },
        {
            "pregunta": "¿Cuanto tiempo tarda la aprobacion?",
            "respuesta": "La precalificacion es inmediata. La aprobacion final por un asesor humano puede tomar de 24 a 48 horas habiles.",
            "palabras_clave": ["tiempo", "tarda", "aprobacion", "demora", "espera"],
        },
        {
            "pregunta": "¿Puedo pagar anticipadamente?",
            "respuesta": "Si, puedes realizar pagos anticipados sin penalidad. El pago anticipado reduce el saldo de capital y los intereses futuros.",
            "palabras_clave": ["anticipado", "adelantar", "pago", "cuota", "prepago"],
        },
    ]

    for faq in faqs:
        keywords = faq["palabras_clave"]
        matched = [kw for kw in keywords if kw in consulta_lower]
        if matched:
            resultados.append(
                {
                    "pregunta": str(faq["pregunta"]),
                    "respuesta": str(faq["respuesta"]),
                    "relevancia": len(matched),
                }
            )

    resultados.sort(key=lambda item: int(item["relevancia"]), reverse=True)

    if not resultados:
        return {
            "encontrado": False,
            "mensaje": "No encontre informacion especifica sobre esa consulta. Te recomiendo hablar con un asesor humano para obtener una respuesta personalizada.",
        }

    return {
        "encontrado": True,
        "resultados": resultados[:3],
        "total_resultados": len(resultados),
    }
