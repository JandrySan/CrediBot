# CrediBot - Contexto Tecnico

Actualizado: 2026-07-12

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
- FAQ/RAG: busqueda por palabras clave con reranking opcional via Groq.
- Sesiones: timeout configurable, restauracion y limpieza de conversaciones abiertas.
- Tiempo real: WebSocket.

## Arquitectura

```text
CrediBot/
|-- backend/                 FastAPI + SQLAlchemy
|   |-- app/api/             webhook whatsapp, dashboard, websocket
|   |-- app/services/
|   |   |-- ai/              IA (gateway, orquestador, detector, extractor, generador)
|   |   |-- audio/           speech-to-text, text-to-speech
|   |   |-- conversation/    orquestador de flujo, servicio de estados, servicio de solicitudes
|   |   |-- rules/           motor de reglas de credito
|   |   |-- tools/           sistema de tools (registro, ejecutor, tools financieras/politicas/cliente)
|   |   |-- websocket/       administrador de conexiones
|   |   `-- whatsapp/        servicio de enrutamiento de mensajes, twilio service
|   |-- app/repositories/    acceso a datos
|   |-- app/models/          entidades SQLAlchemy
|   |-- app/state_machine/   estados y transiciones formales
|   |-- app/database/        engine, session, init
|   `-- tests/               pruebas backend
|-- frontend/                React + TypeScript + MUI
|   |-- src/components/      layout y componentes de conversaciones
|   |-- src/hooks/           hooks de datos y WebSocket
|   |-- src/services/        clientes HTTP
|   |-- src/pages/           dashboard y administracion de FAQs
|   `-- src/types/           tipos TypeScript
|-- README.md
`-- CONTEXT.md
```

## Modelo de datos principal

- `Customer`: cliente, telefono, nombre.
- `Conversation`: conversacion activa, estado, status y resultado.
- `Message`: mensajes inbound/outbound, tipo texto/audio y contenido.
- `CreditApplication`: solicitud de credito, monto, plazo, ingresos, resultado y motivo.
- `AIAnalysis`: resultado del analisis IA por conversacion.
- `ConversationStateHistory`: historial de transiciones de estado.
- `KnowledgeBase`: FAQs activas para politicas, requisitos, tasas, documentos y condiciones.

## Flujo WhatsApp

Archivo: `backend/app/api/whatsapp.py`

El webhook ahora usa `WhatsAppService` para procesar los mensajes:

1. Twilio llama `POST /webhook/whatsapp`.
2. Se valida el remitente (`From`).
3. Si el mensaje trae audio, se descarga con `SpeechToTextService` y se transcribe.
4. Se delega en `WhatsAppService.process_inbound_message()` o `process_audio_transcript()`.
5. `WhatsAppService` internamente usa `ConversationOrchestrator` para el flujo estructurado o `AIOrchestrator` para el modo `AI_ONLY_MODE`.
6. Se genera respuesta de texto.
7. Si `AUDIO_REPLY_ENABLED=true` y `TextToSpeechService.generate_voice_note()` tiene exito, se responde con media; si no, con texto plano.
8. Se emite evento WebSocket `NEW_MESSAGE` o `AUDIO_TRANSCRIPTION_FAILED`.

Nota: el webhook no aplica actualmente una preferencia de respuesta por cliente. La salida de audio depende de la configuracion global `AUDIO_REPLY_ENABLED`.

## Estados de conversacion

Definidos en `backend/app/state_machine/states.py`:

- `START`
- `ASK_NAME`
- `ASK_AMOUNT`
- `ASK_TERM`
- `ASK_INCOME`
- `SHOW_RESULT`
- `HANDOFF`
- `END`

### Reglas de transicion

Archivo: `backend/app/state_machine/transitions.py`

Define `STATE_TRANSITIONS` como un diccionario que mapea cada estado a la lista de estados destino validos:

```text
START       -> ASK_NAME, ASK_AMOUNT, HANDOFF, END
ASK_NAME    -> ASK_AMOUNT, ASK_TERM, ASK_INCOME, SHOW_RESULT, HANDOFF, END
ASK_AMOUNT  -> ASK_TERM, ASK_INCOME, SHOW_RESULT, HANDOFF, END
ASK_TERM    -> ASK_INCOME, SHOW_RESULT, HANDOFF, END
ASK_INCOME  -> SHOW_RESULT, HANDOFF, END
SHOW_RESULT -> HANDOFF, END
HANDOFF     -> END
END         -> (ninguna)
```

El `ConversationOrchestrator._change_state()` valida contra estas reglas antes de ejecutar cualquier transicion. Si la transicion no es valida, lanza `ValueError`.

Funciones disponibles:

- `can_transition(current_state: str, next_state: str) -> bool`
- `is_valid_transition(current: ConversationState, next: ConversationState) -> bool`
- `get_allowed_transitions(state: ConversationState) -> list[ConversationState]`

## Motor de reglas

Archivo: `backend/app/services/rules/credit_rule_engine.py`

Reglas:

- `monthly_income < 600` -> `OBSERVADO`
- `amount > monthly_income * 8` -> `OBSERVADO`
- `term_months > 60` -> `OBSERVADO`
- Caso contrario -> `PREAPROBADO`

La IA no decide la aprobacion. La decision sale del motor de reglas.

## Sistema de Tools

Directorio: `backend/app/services/tools/`

El sistema de tools esta parcialmente implementado. La intencion es permitir que la IA invoque funciones especificas (function calling) para calculos, consultas a DB o busqueda en politicas.

### Arquitectura

- `tool_registry.py` — Registro central singleton. Decorador `@tool(name, description, parameters, requires_db)` para registrar funciones como tools.
- `tool_executor.py` — `ToolExecutor` recibe las `tool_calls` de Groq, busca la tool registrada, la ejecuta y retorna el resultado.
- `tool_registry.to_openai_specs()` — Genera las definiciones en formato JSON Schema que Groq entiende.

Brecha actual: las tools se registran solo cuando se importan sus modulos (`financial_tools.py`, `customer_tools.py`, `policy_tools.py`). Actualmente no hay un import central en startup o en `AIOrchestrator`, por lo que el registro puede quedar vacio.

### Tools registradas

| Tool | Descripcion | Requiere DB |
|---|---|---|
| `calcular_amortizacion(monto, plazo_meses, tasa_interes_anual)` | Calcula cuota mensual, total intereses y tabla mes a mes | No |
| `consultar_estado_cliente(telefono)` | Devuelve datos del cliente e historial de solicitudes | Si |
| `obtener_reglas_credito()` | Devuelve las reglas del motor de precalificacion | No |
| `consultar_politica(consulta)` | Busca en FAQ por palabras clave y devuelve respuestas | No |

### Integracion con IA

Objetivo esperado de `AIGateway.generate_with_tools()`:

1. Enviar las definiciones de tools a Groq via el parametro `tools`.
2. Si la respuesta contiene `tool_calls`, extraer el nombre, argumentos y `tool_call_id`.
3. Ejecutar cada tool mediante `ToolExecutor`.
4. Retroalimentar los resultados a Groq para generar la respuesta final al usuario.
5. Soporta multiples rondas de tool calling (max 5 por defecto).

`AIOrchestrator.generate_whatsapp_reply()` integra todo: recibe el mensaje del usuario, construye el historial, pasa las tools disponibles, y orquesta el ciclo de llamadas automaticamente.

Estado actual: `AIGateway.generate_with_tools()` detecta `tool_calls`, pero no ejecuta las tools dentro del loop y agrega mensajes `tool` vacios. Luego `AIOrchestrator` intenta ejecutar las tools en una segunda etapa. Este flujo necesita correccion para conservar el mensaje assistant con `tool_calls`, ejecutar herramientas con resultados reales y devolver esos resultados al modelo en el formato esperado.

### Como agregar una tool nueva

```python
from app.services.tools.tool_registry import tool

@tool(
    name="mi_tool",
    description="Descripcion clara de lo que hace",
    parameters={
        "type": "object",
        "properties": {
            "param1": {
                "type": "string",
                "description": "Descripcion del parametro",
            },
        },
        "required": ["param1"],
    },
    requires_db=False,  # True si necesita acceso a la BD
)
def mi_tool(param1: str, db=None) -> dict:
    # Si requires_db=True, recibe db: Session automaticamente
    return {"resultado": param1}
```

La tool se registra automaticamente al importar el modulo. Importar en `AIOrchestrator` o en el startup de la app.

## IA

Servicios en `backend/app/services/ai/`:

- `AIGateway`: encapsula llamadas a Groq. Soporta `generate_json()`, `generate_text()`, `generate_chat()` y `generate_with_tools()`.
- `AIOrchestrator`: coordina intencion, extraccion, respuesta y tool calling automatico.
- `IntentDetector`: clasifica intencion (`saludo`, `credito`, `asesor`, `desconocido`).
- `EntityExtractor`: extrae `full_name`, `amount`, `term_months`, `monthly_income`.
- `ResponseGenerator`: pule respuestas sin cambiar datos, resultados ni reglas.

### Modo recomendado

```env
AI_ONLY_MODE=false
```

Con `AI_ONLY_MODE=false` el sistema usa estados y reglas de negocio. Con `AI_ONLY_MODE=true` la IA responde conversacionalmente sin reglas.

Nota: el uso de tools requiere corregir la carga de modulos y el ciclo de tool calling descrito arriba.

## FAQ/RAG

Directorio: `backend/app/services/rag/`

La Fase 3 esta implementada como un sistema FAQ/RAG basico:

- `models.py`: define `KnowledgeBase` con `id`, `question`, `answer`, `category`, `keywords`, `is_active`, `created_at` y `updated_at`.
- `faq_loader.py`: carga FAQs desde JSON o CSV. Acepta campos en ingles (`question`, `answer`, `category`, `keywords`) o espanol (`pregunta`, `respuesta`, `categoria`, `palabras_clave`).
- `retrieval_service.py`: busca FAQs activas por coincidencia de palabras clave y texto. Si Groq esta disponible, intenta reranking con LLM; si no, usa ranking local.
- `embedding_service.py`: placeholder para una futura integracion con embeddings o pgvector.

Endpoints de dashboard:

- `POST /api/dashboard/faq/upload`: carga archivo JSON o CSV.
- `GET /api/dashboard/faq`: lista FAQs activas.
- `DELETE /api/dashboard/faq/{id}`: eliminacion logica, marca `is_active=false`.

Frontend:

- Ruta `/faqs` en `frontend/src/App.tsx`.
- `frontend/src/pages/FaqAdminPage.tsx`: pantalla para cargar JSON/CSV, listar FAQs activas y eliminar FAQs.
- `frontend/src/services/faq.service.ts`: cliente HTTP para endpoints FAQ.
- `frontend/src/hooks/useFaqs.ts`: hooks React Query para listado, carga y eliminacion.
- `frontend/src/types/faq.ts`: tipos `FaqItem` y `FaqUploadResult`.

Integracion conversacional:

- En `AIOrchestrator.generate_whatsapp_reply()`, si hay una sesion DB disponible, `RetrievalService` construye contexto FAQ y lo agrega al prompt del modelo.
- En `ConversationOrchestrator`, si el usuario hace una pregunta sobre requisitos, documentos, tasas, politicas, condiciones o plazo maximo, se busca una FAQ relevante. Si existe, el bot responde esa informacion y ofrece continuar con la precalificacion.
- `ResponseGenerator.generate()` acepta `faq_context` para pulir la respuesta sin inventar datos fuera de la FAQ.

Formato JSON soportado:

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

## WhatsApp Service

Archivo: `backend/app/services/whatsapp/whatsapp_service.py`

`WhatsAppService` centraliza el procesamiento de mensajes entrantes:

- `process_inbound_message(phone_number, text, message_type, profile_name)` — para mensajes de texto.
- `process_audio_transcript(phone_number, transcript_text, profile_name)` — para mensajes de audio transcritos.

Internamente decide si usar `ConversationOrchestrator` (flujo estructurado) o `AIOrchestrator` (modo IA) segun `AI_ONLY_MODE`.

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

Pendiente de implementacion.

La documentacion anterior describia este campo:

```text
customers.preferred_response_type
```

Valores:

- `TEXT`
- `AUDIO`

Pero el modelo `Customer` actual no incluye `preferred_response_type`, `init_db()` no crea ni migra esa columna y el webhook no cambia preferencia por frases del usuario.

Frases deseadas para una implementacion futura:

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

Archivo: `backend/app/api/dashboard.py`

Endpoints:

- `GET /api/dashboard/stats`
- `GET /api/dashboard/conversations`
- `GET /api/dashboard/conversations/{id}/messages`
- `POST /api/dashboard/conversations/{id}/take`
- `POST /api/dashboard/conversations/{id}/reply`
- `POST /api/dashboard/conversations/{id}/close`
- `POST /api/dashboard/conversations/cleanup-expired`
- `POST /api/dashboard/faq/upload`
- `GET /api/dashboard/faq`
- `DELETE /api/dashboard/faq/{id}`

Comportamiento:

- Lista conversaciones con datos de cliente y solicitud.
- Estado actual: si un cliente tiene varias conversaciones o varias solicitudes, puede aparecer mas de una fila para el mismo cliente.
- Permite tomar conversacion como asesor.
- Permite responder al cliente por WhatsApp.
- Permite cerrar conversacion en HANDOFF con resolucion (APPROVED/DENIED/RESOLVED).
- Permite disparar limpieza manual de conversaciones abiertas expiradas.

Frontend:

- `App.tsx` usa `react-router-dom` con rutas `/` y `/faqs`.
- `Sidebar.tsx` navega entre Panel y FAQs.
- `ConversationChat.tsx` soporta un campo opcional `tool_calls` por mensaje y renderiza chips con el nombre de la tool si el backend los devuelve.

Nota: la visualizacion de `tool_calls` ya esta preparada en frontend, pero el backend todavia no persiste tool calls por mensaje.

## Sesiones de conversacion

La Fase 4 esta implementada con timeout configurable, restauracion y limpieza de sesiones.

Configuracion:

```env
CONVERSATION_SESSION_TIMEOUT_MINUTES=60
CONVERSATION_CLEANUP_BATCH_SIZE=100
```

Comportamiento:

- `ConversationRepository.get_or_create_active(customer_id, timeout_minutes=None)` reutiliza una conversacion `ACTIVE` o `HANDOFF` si no expiro.
- Si la conversacion abierta expiro, `ConversationRepository.close_expired()` la marca como `CLOSED`, mueve `current_state` a `END`, asigna `result=EXPIRADO` si no tenia resultado y crea una nueva conversacion `ACTIVE`.
- `ConversationRepository.restore_session(customer_id, timeout_minutes=None)` devuelve la sesion abierta si existe y no expiro; si expiro, la cierra y devuelve `None`.
- `ConversationRepository.cleanup_expired_open_sessions()` cierra sesiones abiertas vencidas por lotes.
- `ConversationManager` expone `restore_session(phone_number)` y `cleanup_expired_sessions()`, usando `CONVERSATION_SESSION_TIMEOUT_MINUTES`.
- `MessageRepository.save_message()` actualiza `conversations.updated_at` para que el timeout se base en actividad real.
- El startup ejecuta una limpieza inicial despues de `init_db()`.

Endpoint operativo:

- `POST /api/dashboard/conversations/cleanup-expired`: cierra conversaciones abiertas expiradas y devuelve `closed_count`.

## Respuesta de asesor humano

Archivo: `backend/app/api/dashboard.py`

Flujo:

1. El asesor envia mensaje desde el dashboard.
2. El backend obtiene la conversacion y cliente.
3. El backend guarda el mensaje como `OUTBOUND`.
4. `TwilioWhatsAppService` intenta enviar el mensaje al numero del cliente.
5. Si Twilio falla, el endpoint devuelve `success=false`, pero el mensaje ya quedo guardado.
6. Se emite evento WebSocket `AGENT_REPLY`.

Pendiente: decidir si el mensaje debe guardarse solo despues de un envio exitoso o si debe persistirse con estado de fallo.

## WebSocket

Archivos:

- `backend/app/api/websocket.py`
- `backend/app/services/websocket/connection_manager.py`
- `frontend/src/hooks/useDashboardSocket.ts`

Eventos relevantes:

- `NEW_MESSAGE`
- `AUDIO_TRANSCRIPTION_FAILED`
- `AGENT_REPLY`
- `CONVERSATION_CLOSED`

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

`init_db()` crea las tablas declaradas en los modelos actuales. No ejecuta migraciones incrementales ni asegura la columna `customers.preferred_response_type`.

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

# Conversation sessions
CONVERSATION_SESSION_TIMEOUT_MINUTES=60
CONVERSATION_CLEANUP_BATCH_SIZE=100

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
- `POST /api/dashboard/conversations/{id}/close`
- `POST /api/dashboard/conversations/cleanup-expired`

### WebSocket

- `GET ws://<host>/ws/dashboard`

## Validacion realizada

- Backend conecta con PostgreSQL.
- `init_db()` ejecuta correctamente.
- Endpoint de conversaciones responde `200`.
- Frontend compila con `npm run build`.
- Pruebas backend pasan con `DEBUG=false` inyectado en el entorno: `23 passed`.
- Flujo de audio esta cubierto por pruebas.
- Maquina de estados con transiciones validadas.
- FAQ/RAG esta cubierto por pruebas unitarias de carga y busqueda.
- Sesiones de conversacion estan cubiertas por pruebas de restauracion, expiracion y limpieza.
- Frontend de administracion de FAQs compila con `npm run build`.

Estado actual de pruebas backend:

- Al ejecutar `.\.venv\Scripts\python.exe -m pytest tests -q` desde `backend/`, la coleccion falla si `backend/.env` contiene `DEBUG=release`.
- `settings.DEBUG` esta tipado como booleano, por lo que debe usar valores como `true` o `false`, o debe aislarse la configuracion de test.

## Brechas pendientes

- Completar credenciales reales de Twilio y Groq.
- Corregir `DEBUG` en `backend/.env` para permitir ejecucion de tests.
- Configurar `TWILIO_WEBHOOK_URL` con ngrok o dominio publico.
- Implementar o retirar la preferencia por cliente para texto/audio.
- Cargar automaticamente los modulos de tools y corregir el ciclo completo de tool calling.
- Alinear el guardado de mensajes del asesor con el resultado real de Twilio.
- Deduplicar conversaciones por cliente en dashboard si ese sigue siendo el comportamiento esperado.
- Validar firma de webhook de Twilio.
- Autenticacion y autorizacion del dashboard.
- Rate limiting y endurecimiento de seguridad.
- Despliegue productivo y observabilidad.

## Notas para nuevos colaboradores

- Para agregar una tool: crear funcion con decorador `@tool()` en `backend/app/services/tools/` y asegurar que se importe en el startup de la app o en `AIOrchestrator`.
- Las tools que requieren DB deben tener `requires_db=True` y recibir `db` como parametro. El `ToolExecutor` inyecta la sesion automaticamente.
- La maquina de estados valida transiciones en runtime. Si una transicion no es valida, el sistema lanza `ValueError`. Revisar `transitions.py` para ver las reglas.
- Los tests se ejecutan con `pytest backend/tests/ -v` desde la carpeta `backend/`.
