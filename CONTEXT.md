# CrediBot - Contexto tecnico

Actualizado: 2026-07-13

## Resumen

CrediBot es un MVP de asistente de precalificacion de creditos por WhatsApp.
Automatiza la captura inicial de datos, consulta una central de riesgo simulada,
aplica reglas de negocio y permite intervencion humana desde un dashboard.

El proyecto no tiene app movil. El producto actual es:

- Backend FastAPI.
- Dashboard web React.
- WhatsApp por Twilio Sandbox.
- PostgreSQL en Supabase.
- Despliegue AWS con ECS, ECR, S3 y CloudFront.

## Estado productivo

Servicios actuales:

- Frontend: `https://d30z3dsmpm7ctx.cloudfront.net`
- API: `https://d30z3dsmpm7ctx.cloudfront.net/api/...`
- Webhook: `https://d30z3dsmpm7ctx.cloudfront.net/webhook/whatsapp`
- Audios: `https://d30z3dsmpm7ctx.cloudfront.net/webhook/audio/{filename}`
- Supabase project ref: `subcovtwgoqbitvzoyzy`
- ECS cluster: `credibot-cluster`
- ECS service: `credibot-backend-service`
- ECR repository: `credibot-backend`
- Twilio Sandbox: `whatsapp:+14155238886`

## Stack

- Backend: FastAPI, SQLAlchemy, Pydantic Settings.
- Base de datos: PostgreSQL/Supabase.
- Frontend: React, TypeScript, Vite, MUI, React Query.
- WhatsApp: Twilio Sandbox.
- IA: Groq.
- STT: Groq por defecto, faster-whisper local opcional.
- TTS: gTTS + conversion a OGG/Opus con PyAV.
- FAQ/RAG: busqueda por palabras clave con reranking opcional via Groq.
- Tiempo real: WebSocket.
- CI/CD: GitHub Actions.
- AWS: OIDC, ECR, ECS Fargate, ALB, S3, CloudFront, Secrets Manager.

## Estructura

```text
CrediBot/
|-- backend/
|   |-- app/api/             webhook, dashboard, websocket
|   |-- app/database/        engine, sesiones e inicializacion incremental
|   |-- app/models/          modelos SQLAlchemy
|   |-- app/repositories/    acceso a datos
|   |-- app/services/
|   |   |-- ai/              Groq, intencion, extraccion, respuesta
|   |   |-- audio/           STT y TTS
|   |   |-- conversation/    orquestador, estados, solicitud de credito
|   |   |-- credit_bureau/   consulta a central simulada
|   |   |-- rag/             FAQ/RAG
|   |   |-- rules/           reglas de precalificacion
|   |   |-- tools/           tools para IA
|   |   |-- websocket/       broadcaster
|   |   `-- whatsapp/        Twilio y preferencias texto/audio
|   |-- app/state_machine/   estados y transiciones
|   `-- tests/               pruebas backend
|-- frontend/                dashboard React
|-- supabase/migrations/     schema y datos simulados
|-- docs/                    documentacion operativa
|-- .github/workflows/       CI/CD
|-- README.md
`-- CONTEXT.md
```

## Modelo de datos principal

- `Customer`: telefono, cedula (`national_id`) y nombre.
- `Conversation`: estado, status, resultado y `response_mode`.
- `Message`: mensajes inbound/outbound, texto/audio.
- `CreditApplication`: monto, plazo, ingreso, resultado y motivo.
- `AIAnalysis`: resultado del analisis IA.
- `ConversationStateHistory`: historial de transiciones.
- `KnowledgeBase`: FAQs activas.

Inicializacion incremental:

- `customers.national_id` se agrega si falta.
- `idx_customers_national_id` se crea si falta.
- `conversations.response_mode` se agrega si falta.
- `credit_applications.reason` se convierte a `TEXT` en PostgreSQL si estaba
  limitado.

## Central de riesgo simulada

Schema: `credit_bureau`.

Objetos:

- `people`
- `credit_accounts`
- `payment_history`
- `credit_score_snapshots`
- `risk_events`
- `credit_inquiries`
- `credit_profile_summary`
- `find_profile(identifier TEXT)`

La funcion `find_profile` acepta cedula o telefono y devuelve un perfil
normalizado para CrediBot. El servicio que la consume esta en:

```text
backend/app/services/credit_bureau/profile_service.py
```

Campos importantes:

- Identidad: cedula, telefono, nombre, edad, provincia, ciudad.
- Trabajo: estado laboral, ocupacion, ingreso reportado.
- Central: estado, motivo, score, riesgo.
- Deuda: cuentas, deuda pendiente, cuota mensual, relacion deuda/ingreso.
- Mora: mora maxima, pagos incumplidos, pagos tardios.
- Eventos: castigados, judiciales, reestructurados.
- Consultas recientes.
- Cuota maxima recomendada.
- Resultado preliminar: `APTO` u `OBSERVADO`.

Consulta de prueba:

```sql
SELECT *
FROM credit_bureau.find_profile('9990000003');
```

Resultado esperado resumido:

```text
Maria Torres Cedeno
score: 485
risk_level: HIGH
deuda: 2100
mora maxima: 90
resultado: OBSERVADO
```

## Flujo WhatsApp

Archivo principal:

```text
backend/app/api/whatsapp.py
```

Pasos:

1. Twilio llama `POST /webhook/whatsapp`.
2. Se valida `From`.
3. Se detecta audio entrante y se transcribe si aplica.
4. Se detecta cambio de preferencia: audio/texto.
5. Se delega a `WhatsAppService`.
6. `WhatsAppService` usa `ConversationOrchestrator`.
7. Se guarda mensaje inbound.
8. La IA clasifica intencion y extrae entidades.
9. El orquestador rellena campos, consulta central y cambia estados.
10. Si la solicitud esta completa, se evalua.
11. Se guarda mensaje outbound.
12. Se responde por texto o por audio segun `response_mode`.
13. Se emite evento WebSocket.

## Estados

Definidos en `backend/app/state_machine/states.py`:

- `START`
- `ASK_NATIONAL_ID`
- `ASK_NAME`
- `ASK_AMOUNT`
- `ASK_TERM`
- `ASK_INCOME`
- `SHOW_RESULT`
- `HANDOFF`
- `END`

Transiciones principales:

```text
START           -> ASK_NATIONAL_ID, ASK_NAME, ASK_AMOUNT, HANDOFF, END
ASK_NATIONAL_ID -> ASK_NAME, ASK_AMOUNT, ASK_TERM, ASK_INCOME, SHOW_RESULT, HANDOFF, END
ASK_NAME        -> ASK_AMOUNT, ASK_TERM, ASK_INCOME, SHOW_RESULT, HANDOFF, END
ASK_AMOUNT      -> ASK_TERM, ASK_INCOME, SHOW_RESULT, HANDOFF, END
ASK_TERM        -> ASK_INCOME, SHOW_RESULT, HANDOFF, END
ASK_INCOME      -> SHOW_RESULT, HANDOFF, END
SHOW_RESULT     -> HANDOFF, END
HANDOFF         -> END
END             -> ninguna
```

`ConversationOrchestrator._change_state()` valida las transiciones en runtime.

## Extraccion de datos

Archivo:

```text
backend/app/services/ai/entity_extractor.py
```

Entidades:

- `national_id`
- `full_name`
- `amount`
- `term_months`
- `monthly_income`

El orquestador tiene fallback local para extraer cedula, monto, plazo y nombre
cuando la IA no devuelve el campo esperado.

## Evaluacion de credito

Reglas base:

- `monthly_income < 600` -> `OBSERVADO`
- `amount > monthly_income * 8` -> `OBSERVADO`
- `term_months > 60` -> `OBSERVADO`
- Caso contrario -> `PREAPROBADO`

Luego:

- Si la central simulada devuelve `preliminary_history_result=OBSERVADO`, el
  resultado final queda `OBSERVADO`.
- El motivo incluye estado central, riesgo, score, deuda, mora, pagos
  incumplidos y razones de riesgo.

Archivos:

- `backend/app/services/rules/credit_rule_engine.py`
- `backend/app/services/conversation/credit_application_service.py`

## Audio

Entrada:

- `SpeechToTextService` descarga audio desde Twilio.
- Proveedores: `groq`, `local`, `groq_local_fallback`.
- La transcripcion entra al flujo normal.

Salida:

- `TextToSpeechService` genera MP3 con gTTS.
- Convierte a OGG/Opus.
- Sirve el archivo en `GET /webhook/audio/{filename}`.
- Twilio recibe `<Media>URL</Media>`.

Preferencia:

- Se guarda en `conversations.response_mode`.
- Valores: `TEXT`, `AUDIO`.
- `responde en audio` activa audio.
- `responde en texto` vuelve a texto.
- Recibir una nota de voz no obliga al bot a contestar en audio.

## FAQ/RAG

Directorio:

```text
backend/app/services/rag/
```

Endpoints:

- `POST /api/dashboard/faq/upload`
- `GET /api/dashboard/faq`
- `DELETE /api/dashboard/faq/{id}`

Formato JSON:

```json
[
  {
    "question": "Cuales son los requisitos?",
    "answer": "Documento de identidad e ingresos comprobables.",
    "category": "requisitos",
    "keywords": ["requisitos", "documentos"]
  }
]
```

La busqueda se usa para preguntas sobre requisitos, documentos, tasas,
politicas, condiciones y plazo maximo.

## Sistema de tools

Directorio:

```text
backend/app/services/tools/
```

Tools actuales:

- `calcular_amortizacion`
- `consultar_estado_cliente`
- `obtener_reglas_credito`
- `consultar_politica`
- `consultar_central_riesgo`

La integracion de tool calling ya evita respuestas tecnicas de tags internos,
pero sigue siendo un area candidata a endurecimiento con mas pruebas de
conversaciones largas.

## Dashboard

Backend:

```text
backend/app/api/dashboard.py
```

Frontend:

```text
frontend/src
```

Funciones:

- Estadisticas.
- Lista de conversaciones.
- Detalle de chat.
- Cedula y datos de solicitud.
- Handoff y respuesta de asesor.
- Cierre de conversacion.
- Limpieza de expiradas.
- CRUD logico de FAQs.
- WebSocket para eventos.

Nota: el endpoint de conversaciones puede devolver mas de una fila por cliente
si hay varias conversaciones o solicitudes.

## WebSocket

Endpoint:

```text
/ws/dashboard
```

Eventos:

- `NEW_MESSAGE`
- `AUDIO_TRANSCRIPTION_FAILED`
- `AGENT_REPLY`
- `CONVERSATION_CLOSED`

`NEW_MESSAGE` incluye:

- `bot_response_type`: `TEXT`, `AUDIO` o `NONE`.
- `bot_response_mode`: `TEXT` o `AUDIO`.
- `bot_media_url`.
- `bot_audio_error`.

## Sesiones

Variables:

```env
CONVERSATION_SESSION_TIMEOUT_MINUTES=60
CONVERSATION_CLEANUP_BATCH_SIZE=100
ABANDONED_CONVERSATION_RETENTION_DAYS=7
```

Comportamiento:

- Se reutiliza conversacion abierta si no expiro.
- Si expiro, se cierra como `EXPIRADO` y se crea una nueva.
- La limpieza inicial corre en startup.
- Hay endpoint manual para limpiar expiradas.
- Se purgan conversaciones cerradas por abandono despues del periodo definido.

## Variables principales

Backend:

```env
DATABASE_URL=
SUPABASE_DATABASE_URL=
GROQ_API_KEY=
AI_ONLY_MODE=false
BACKEND_CORS_ORIGINS=https://d30z3dsmpm7ctx.cloudfront.net

TWILIO_ENABLED=true
TWILIO_ACCOUNT_SID=AC...
TWILIO_AUTH_TOKEN=
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
TWILIO_WHATSAPP_NUMBER=+14155238886
TWILIO_WEBHOOK_URL=https://d30z3dsmpm7ctx.cloudfront.net/webhook/whatsapp

AUDIO_STT_ENABLED=true
AUDIO_STT_PROVIDER=groq
AUDIO_REPLY_ENABLED=true
AUDIO_REPLY_LANGUAGE=es
AUDIO_REPLY_PUBLIC_BASE_URL=https://d30z3dsmpm7ctx.cloudfront.net
```

Frontend:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
VITE_WS_BASE_URL=ws://127.0.0.1:8000
```

## CI/CD

Workflows:

- `ci-backend.yml`: instala dependencias, compila Python y corre pruebas.
- `ci-frontend.yml`: `npm ci`, lint y build.
- `cd-backend-aws.yml`: build/push Docker en ECR, registra task definition y
  actualiza ECS.
- `cd-frontend-aws.yml`: build frontend, sync a S3 e invalidacion CloudFront.

El CD backend reutiliza la task definition activa, cambia imagen y asegura las
variables no secretas de respuesta por voz.

## Validacion actual

Validado el 2026-07-13:

- Supabase migrado.
- Backend local: 49 pruebas.
- Frontend local: lint y build correctos.
- CI/CD backend y frontend correctos.
- CloudFront responde API.
- Webhook responde texto.
- `responde en audio` devuelve `<Media>` con `audio/ogg`.
- Flujo con cedula `9990000003` autocompleta nombre y termina `OBSERVADO`.

## Pendientes

- Dominio propio y certificado ACM.
- Validacion de firma Twilio.
- Autenticacion y roles del dashboard.
- Rate limiting.
- Alarmas CloudWatch.
- Separacion staging/prod.
- Rotacion periodica de secretos.
- Estado de envio para mensajes de asesor.
- Deduplicacion o agrupacion por cliente en dashboard.
