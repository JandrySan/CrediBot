# CrediBot - Contexto Tecnico

Actualizado: 2026-07-09

## Resumen

CrediBot es un MVP de asistente de precalificacion de creditos por WhatsApp. Automatiza la captura inicial de datos, permite mensajes de texto y audio, aplica reglas de negocio para entregar un resultado preliminar y ofrece un dashboard para que un asesor humano intervenga cuando sea necesario.

## Stack

- Backend: FastAPI, SQLAlchemy, Pydantic Settings.
- Base de datos: PostgreSQL.
- Frontend: React, TypeScript, Vite, MUI, React Query.
- WhatsApp: Twilio Sandbox.
- IA: Groq.
- Audio STT: Groq por defecto, faster-whisper local opcional.
- Audio TTS: gTTS + conversion a OGG/Opus con PyAV.
- Tiempo real: WebSocket.

## Arquitectura

```text
CrediBot/
|-- backend/                 FastAPI + SQLAlchemy
|   |-- app/api/             webhook whatsapp, dashboard, websocket
|   |-- app/services/        IA, orquestacion, reglas, audio, twilio, websocket
|   |-- app/repositories/    acceso a datos
|   |-- app/models/          entidades SQLAlchemy
|   |-- app/database/        engine, session, init
|   `-- tests/               pruebas backend
|-- frontend/                React + TypeScript + MUI
|   |-- src/components/      layout y componentes de conversaciones
|   |-- src/hooks/           hooks de datos y WebSocket
|   |-- src/services/        clientes HTTP
|   `-- src/types/           tipos TypeScript
|-- README.md
`-- CONTEXT.md
```

## Modelo de datos principal

- `Customer`: cliente, telefono, nombre y preferencia de respuesta (`TEXT` o `AUDIO`).
- `Conversation`: conversacion activa, estado, status y resultado.
- `Message`: mensajes inbound/outbound, tipo texto/audio y contenido.
- `CreditApplication`: solicitud de credito, monto, plazo, ingresos, resultado y motivo.
- `AIAnalysis`: resultado del analisis IA por conversacion.
- `ConversationStateHistory`: historial de transiciones de estado.

## Flujo WhatsApp

1. Twilio llama `POST /webhook/whatsapp`.
2. El backend valida el remitente.
3. Si el mensaje trae audio, se descarga y transcribe.
4. Se normaliza el telefono.
5. Se obtiene o crea `Customer`.
6. Se obtiene o crea conversacion abierta.
7. Se obtiene o crea solicitud de credito vigente.
8. Se guarda el mensaje inbound.
9. Se detecta si el cliente pidio respuesta en audio o texto.
10. Se analiza intencion y entidades con IA.
11. Se guardan datos extraidos.
12. Si falta informacion, se pregunta el siguiente campo.
13. Si la solicitud esta completa, se aplica el motor de reglas.
14. Se guarda la respuesta outbound.
15. Se responde a Twilio con TwiML de texto o media.
16. Se emite evento WebSocket para el dashboard.

## Estados de conversacion

Definidos en `backend/app/state_machine/states.py`:

- `START`
- `ASK_NAME`
- `ASK_AMOUNT`
- `ASK_TERM`
- `ASK_INCOME`
- `SHOW_RESULT`
- `HANDOFF`

## Motor de reglas

Archivo: `backend/app/services/rules/credit_rule_engine.py`

Reglas:

- `monthly_income < 600` -> `OBSERVADO`
- `amount > monthly_income * 8` -> `OBSERVADO`
- `term_months > 60` -> `OBSERVADO`
- Caso contrario -> `PREAPROBADO`

La IA no decide la aprobacion. La decision sale del motor de reglas.

## IA

Servicios:

- `AIGateway`: encapsula llamadas a Groq.
- `AIOrchestrator`: coordina intencion, extraccion y respuesta.
- `IntentDetector`: clasifica intencion (`saludo`, `credito`, `asesor`, `desconocido`).
- `EntityExtractor`: extrae `full_name`, `amount`, `term_months`, `monthly_income`.
- `ResponseGenerator`: pule respuestas sin cambiar datos, resultados ni reglas.

Modo recomendado:

```env
AI_ONLY_MODE=false
```

Con este modo, el sistema usa estados y reglas de negocio. `AI_ONLY_MODE=true` deja una respuesta conversacional sin reglas y no es el modo recomendado para defender el MVP de credito.

## Audio

### Entrada

Archivo: `backend/app/services/audio/speech_to_text.py`

- Descarga media desde Twilio.
- Soporta proveedor `groq`, `local` y `groq_local_fallback`.
- Retorna texto transcrito para procesarlo como mensaje normal.

### Salida

Archivo: `backend/app/services/audio/text_to_speech.py`

- Genera MP3 con gTTS.
- Convierte MP3 a OGG/Opus.
- Construye URL publica para Twilio.
- Limpia audios antiguos.

Endpoint publico:

```text
GET /webhook/audio/{filename}
```

## Preferencia texto/audio

Campo:

```text
customers.preferred_response_type
```

Valores:

- `TEXT`
- `AUDIO`

Frases que activan audio:

- "respondeme en audio"
- "quiero que me respondas en audio"
- "nota de voz"
- "por audio"

Frases que vuelven a texto:

- "respondeme en texto"
- "solo texto"
- "no me respondas en audio"
- "sin audio"

## Dashboard

Endpoints:

- `GET /api/dashboard/stats`
- `GET /api/dashboard/conversations`
- `GET /api/dashboard/conversations/{id}/messages`
- `POST /api/dashboard/conversations/{id}/take`
- `POST /api/dashboard/conversations/{id}/reply`

Comportamiento:

- Lista conversaciones con datos de cliente y solicitud.
- Devuelve solo una conversacion por cliente para evitar duplicados.
- Usa la conversacion mas reciente y la solicitud mas reciente.
- Permite tomar conversacion como asesor.
- Permite responder al cliente por WhatsApp.

## Respuesta de asesor humano

Archivo: `backend/app/api/dashboard.py`

Flujo:

1. El asesor envia mensaje desde el dashboard.
2. El backend obtiene la conversacion y cliente.
3. `TwilioWhatsAppService` envia el mensaje al numero del cliente.
4. Si Twilio responde exito, se guarda el mensaje como `OUTBOUND`.
5. Si Twilio falla, no se guarda como enviado.
6. Se emite evento WebSocket `AGENT_REPLY`.

## WebSocket

Archivos:

- `backend/app/api/websocket.py`
- `backend/app/services/websocket/connection_manager.py`
- `frontend/src/hooks/useDashboardSocket.ts`

Eventos relevantes:

- `NEW_MESSAGE`
- `AUDIO_TRANSCRIPTION_FAILED`
- `AGENT_REPLY`

Uso:

- Mantener actualizado el dashboard sin depender solo del polling.
- Notificar nuevos mensajes o respuestas.

## Base de datos

Configuracion:

```env
DATABASE_URL=
DB_HOST=localhost
DB_PORT=5432
DB_NAME=credibot
DB_USER=postgres
DB_PASSWORD=12345678
```

Si `DATABASE_URL` esta vacio, se construye:

```text
postgresql+psycopg2://<DB_USER>:<DB_PASSWORD>@<DB_HOST>:<DB_PORT>/<DB_NAME>
```

`init_db()` crea tablas y asegura la columna `customers.preferred_response_type` en bases existentes.

## Variables de entorno importantes

```env
# DB
DATABASE_URL=
DB_HOST=localhost
DB_PORT=5432
DB_NAME=credibot
DB_USER=postgres
DB_PASSWORD=12345678

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

# Audio reply
AUDIO_REPLY_ENABLED=true
AUDIO_REPLY_LANGUAGE=es
AUDIO_REPLY_PUBLIC_BASE_URL=

# Twilio
TWILIO_ENABLED=true
TWILIO_ACCOUNT_SID=AC...
TWILIO_AUTH_TOKEN=
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
TWILIO_WHATSAPP_NUMBER=+14155238886
TWILIO_WEBHOOK_URL=https://.../webhook/whatsapp
```

## Endpoints

### App

- `GET /`
- `GET /health`

### WhatsApp

- `POST /webhook/whatsapp`
- `GET /webhook/audio/{filename}`

### Dashboard

- `GET /api/dashboard/stats`
- `GET /api/dashboard/conversations`
- `GET /api/dashboard/conversations/{id}/messages`
- `POST /api/dashboard/conversations/{id}/take`
- `POST /api/dashboard/conversations/{id}/reply`

### WebSocket

- `GET ws://<host>/ws/dashboard`

## Validacion realizada

- Backend conecta con PostgreSQL.
- `init_db()` ejecuta correctamente.
- Endpoint de conversaciones responde `200`.
- Dashboard devuelve una fila por cliente.
- Pruebas backend pasan.
- Frontend compila.
- Flujo de audio esta cubierto por pruebas.
- Preferencia texto/audio esta cubierta por pruebas.

## Brechas pendientes

- Completar credenciales reales de Twilio y Groq.
- Configurar `TWILIO_WEBHOOK_URL` con ngrok o dominio publico.
- Validar firma de webhook de Twilio.
- Autenticacion y autorizacion del dashboard.
- Rate limiting y endurecimiento de seguridad.
- Despliegue productivo y observabilidad.
