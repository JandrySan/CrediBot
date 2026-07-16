# Plantillas transaccionales de WhatsApp

Fecha: 15 de julio de 2026.  
Historia relacionada: US-16.

CrediBot mantiene un catálogo versionado en
`backend/app/services/whatsapp/templates.py`. Las plantillas tienen un identificador
estable, versión, contrato de variables y texto alternativo para el Twilio Sandbox.

## Catálogo

| Clave | Versión | Momento de envío | Variables |
| --- | --- | --- | --- |
| `handoff_requested` | 1.0 | El usuario solicita atención humana | Ninguna |
| `advisor_assigned` | 1.0 | Un asesor toma el caso | `advisor_name` |
| `prequalification_recorded` | 1.0 | Se confirma una simulación registrada | `application_reference`, `result` |

## Estrategia por entorno

### Sandbox académico

Dentro de la sesión del Twilio Sandbox se envía el texto renderizado por el catálogo.
Esto permite demostrar las confirmaciones sin comprar un número ni someter contenido a
aprobación externa.

### Cuenta productiva

Cuando Meta/Twilio exige una plantilla aprobada, se configura su `ContentSid` mediante
un único mapa JSON no secreto:

```env
TWILIO_CONTENT_TEMPLATE_SIDS={"handoff_requested":"HX...","advisor_assigned":"HX...","prequalification_recorded":"HX..."}
```

Si una clave tiene `ContentSid`, el servicio envía `content_sid` y
`content_variables`. Si no lo tiene, usa el texto alternativo versionado. La variable
es opcional y su ausencia no afecta el Sandbox.

## Gobierno de cambios

1. No se modifica el significado de una versión publicada.
2. Un cambio de intención o variables requiere una versión nueva.
3. El texto nunca promete aprobación definitiva ni desembolso.
4. Las variables se validan como completas, no vacías y sin campos inesperados.
5. Cada plantilla nueva requiere pruebas de renderizado y transporte Twilio.

## Pruebas

`backend/tests/test_whatsapp_transactional_templates.py` verifica:

- contrato y versión;
- variables faltantes, vacías o inesperadas;
- renderizado de texto para Sandbox;
- conversión de variables nombradas a posiciones de Twilio;
- envío por texto y por `ContentSid`.

Además, el flujo confirma inmediatamente la solicitud de asesor y permanece silencioso
en los mensajes posteriores hasta que una persona tome o cierre el caso.
