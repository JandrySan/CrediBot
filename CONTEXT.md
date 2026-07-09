# CrediBot - Contexto Tecnico

Actualizado: 2026-07-08

## Resumen

CrediBot es un asistente de precalificacion de creditos por WhatsApp.

Capacidades actuales:

- Conversacion automatica por WhatsApp via Twilio.
- Recepcion de audio por WhatsApp con transcripcion a texto.
- Respuesta de bot por WhatsApp como nota de voz (audio OGG/Opus).
- Extraccion de datos con IA (Groq).
- Flujo por estados para capturar datos minimos.
- Evaluacion de reglas de negocio.
- Respuestas con resumen de datos registrados del usuario.
- Persistencia de clientes, conversaciones, mensajes y analisis IA.
- Dashboard para seguimiento y respuesta humana.

## Arquitectura

```text
CrediBot/
├── backend/                 FastAPI + SQLAlchemy
│   ├── app/api/             webhook whatsapp, dashboard, websocket
│   ├── app/services/        IA, orquestacion, reglas, twilio, websocket
│   ├── app/repositories/    acceso a datos
│   ├── app/models/          entidades SQLAlchemy
│   └── app/database/        engine, session, init
├── frontend/                React + TypeScript + MUI
└── README.md / CONTEXT.md
```

## Modelo de datos principal

- `Customer`
- `Conversation`
- `Message`
- `CreditApplication`
- `AIAnalysis`
- `ConversationStateHistory`

## Flujo funcional actual

1. Twilio envia un mensaje al webhook `POST /webhook/whatsapp`.
2. Se normaliza telefono y se obtiene/crea cliente.
3. Se obtiene/crea conversacion abierta y solicitud de credito.
4. Si llega audio, se descarga desde Twilio y se transcribe.
5. Se guarda mensaje inbound (TEXT o AUDIO).
6. Se analiza mensaje con IA:
   - intencion
   - nombre
   - monto
   - plazo
   - ingresos
7. Se aplica extraccion a entidades.
8. Si faltan datos, se pregunta el siguiente campo requerido.
9. Si ya hay datos completos, se ejecuta motor de reglas y se responde resultado.
10. La respuesta outbound se envia como texto o audio (segun configuracion) y se retorna TwiML a Twilio.
11. Se emite evento por WebSocket para actualizar dashboard.
12. Cada respuesta incluye un resumen de datos ya capturados (nombre, monto, plazo, ingresos).

## Estados de conversacion

- `START`
- `ASK_NAME`
- `ASK_AMOUNT`
- `ASK_TERM`
- `ASK_INCOME`
- `SHOW_RESULT`
- `HANDOFF`

## Motor de reglas

Reglas activas en `CreditRuleEngine`:

- `monthly_income < 600` -> `OBSERVADO`
- `amount > monthly_income * 8` -> `OBSERVADO`
- `term_months > 60` -> `OBSERVADO`
- caso contrario -> `PREAPROBADO`

## IA y modos de operacion

Variable de control: `AI_ONLY_MODE`

- `false` (default): usa flujo completo con estados + reglas.
- `true`: responde solo con IA conversacional (sin reglas de negocio).

Servicios IA relevantes:

- `AIGateway`
- `AIOrchestrator`
- `IntentDetector`
- `EntityExtractor`
- `ResponseGenerator`

## Base de datos en local

Se admite configuracion por `DATABASE_URL`.

Ejemplo para pruebas internas sin PostgreSQL:

```env
DATABASE_URL=sqlite:///./credibot.db
```

Si `DATABASE_URL` no esta definido, se usa configuracion PostgreSQL clasica (`DB_HOST`, `DB_PORT`, etc).

## Variables de entorno importantes

```env
# DB
DATABASE_URL=
DB_HOST=localhost
DB_PORT=5432
DB_NAME=credibot
DB_USER=postgres
DB_PASSWORD=

# IA
GROQ_API_KEY=
AI_ONLY_MODE=false

# Audio STT
AUDIO_STT_ENABLED=true
AUDIO_STT_PROVIDER=groq
AUDIO_STT_MODEL=base
AUDIO_STT_LANGUAGE=es
AUDIO_STT_DEVICE=cpu
AUDIO_STT_COMPUTE_TYPE=int8
AUDIO_STT_GROQ_MODEL=whisper-large-v3-turbo
AUDIO_STT_REQUEST_TIMEOUT_SECONDS=20

# Audio reply (bot -> voice note)
AUDIO_REPLY_ENABLED=true
AUDIO_REPLY_LANGUAGE=es
AUDIO_REPLY_PUBLIC_BASE_URL=

# Twilio
TWILIO_ENABLED=true
TWILIO_ACCOUNT_SID=AC...
TWILIO_AUTH_TOKEN=...
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
TWILIO_WHATSAPP_NUMBER=+14155238886
TWILIO_WEBHOOK_URL=https://.../webhook/whatsapp
```

Si `AUDIO_REPLY_PUBLIC_BASE_URL` queda vacio, se deriva automaticamente desde `TWILIO_WEBHOOK_URL`.

## Dashboard

Endpoints:

- `GET /api/dashboard/stats`
- `GET /api/dashboard/conversations`
- `GET /api/dashboard/conversations/{id}/messages`
- `POST /api/dashboard/conversations/{id}/take`
- `POST /api/dashboard/conversations/{id}/reply`

WebSocket:

- `GET ws://<host>/ws/dashboard`

## Validacion ya realizada

- Flujo WhatsApp en modo negocio (`AI_ONLY_MODE=false`) validado.
- Resultado `PREAPROBADO` validado.
- Resultado `OBSERVADO` validado.
- Twilio autenticado y webhook devolviendo TwiML valido.
- Webhook de audio validado (transcripcion exitosa y manejo de error).

## Brechas pendientes

- Firma de webhook de Twilio.
- Login/JWT/roles en dashboard.
- Politicas de seguridad y rate limiting.
- Despliegue productivo y observabilidad.
