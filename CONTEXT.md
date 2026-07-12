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

## Flujo WhatsApp

Archivo: `backend/app/api/whatsapp.py`

El webhook ahora usa `WhatsAppService` para procesar los mensajes:

1. Twilio llama `POST /webhook/whatsapp`.
2. Se valida el remitente (`From`).
3. Si el mensaje trae audio, se descarga con `SpeechToTextService` y se transcribe.
4. Se delega en `WhatsAppService.process_inbound_message()` o `process_audio_transcript()`.
5. `WhatsAppService` internamente usa `ConversationOrchestrator` para el flujo estructurado o `AIOrchestrator` para el modo `AI_ONLY_MODE`.
6. Se genera respuesta de texto.
7. Si `TextToSpeechService.generate_voice_note()` tiene exito, se responde con media; si no, con texto plano.
8. Se emite evento WebSocket `NEW_MESSAGE` o `AUDIO_TRANSCRIPTION_FAILED`.

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

El sistema de tools permite que la IA invoque funciones especificas (function calling) de forma automatica. Cuando el usuario hace una pregunta que requiere calculos, consultas a DB o busqueda en politicas, la IA detecta la intencion y llama a la tool correspondiente.

### Arquitectura

- `tool_registry.py` — Registro central singleton. Decorador `@tool(name, description, parameters, requires_db)` para registrar funciones como tools.
- `tool_executor.py` — `ToolExecutor` recibe las `tool_calls` de Groq, busca la tool registrada, la ejecuta y retorna el resultado.
- `tool_registry.to_openai_specs()` — Genera las definiciones en formato JSON Schema que Groq entiende.

### Tools registradas

| Tool | Descripcion | Requiere DB |
|---|---|---|
| `calcular_amortizacion(monto, plazo_meses, tasa_interes_anual)` | Calcula cuota mensual, total intereses y tabla mes a mes | No |
| `consultar_estado_cliente(telefono)` | Devuelve datos del cliente e historial de solicitudes | Si |
| `obtener_reglas_credito()` | Devuelve las reglas del motor de precalificacion | No |
| `consultar_politica(consulta)` | Busca en FAQ por palabras clave y devuelve respuestas | No |

### Integracion con IA

`AIGateway.generate_with_tools()` extiende `generate_chat()` para:

1. Enviar las definiciones de tools a Groq via el parametro `tools`.
2. Si la respuesta contiene `tool_calls`, extraer el nombre, argumentos y `tool_call_id`.
3. Ejecutar cada tool mediante `ToolExecutor`.
4. Retroalimentar los resultados a Groq para generar la respuesta final al usuario.
5. Soporta multiples rondas de tool calling (max 5 por defecto).

`AIOrchestrator.generate_whatsapp_reply()` integra todo: recibe el mensaje del usuario, construye el historial, pasa las tools disponibles, y orquesta el ciclo de llamadas automaticamente.

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

Con `AI_ONLY_MODE=false` el sistema usa estados y reglas de negocio. Las tools funcionan en ambos modos.
Con `AI_ONLY_MODE=true` la IA responde conversacionalmente sin reglas y tambien puede usar tools.

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

Archivo: `backend/app/api/dashboard.py`

Endpoints:

- `GET /api/dashboard/stats`
- `GET /api/dashboard/conversations`
- `GET /api/dashboard/conversations/{id}/messages`
- `POST /api/dashboard/conversations/{id}/take`
- `POST /api/dashboard/conversations/{id}/reply`
- `POST /api/dashboard/conversations/{id}/close`

Comportamiento:

- Lista conversaciones con datos de cliente y solicitud.
- Devuelve solo una conversacion por cliente para evitar duplicados.
- Usa la conversacion mas reciente y la solicitud mas reciente.
- Permite tomar conversacion como asesor.
- Permite responder al cliente por WhatsApp.
- Permite cerrar conversacion en HANDOFF con resolucion (APPROVED/DENIED/RESOLVED).

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
- `POST /api/dashboard/conversations/{id}/close`

### WebSocket

- `GET ws://<host>/ws/dashboard`

## Validacion realizada

- Backend conecta con PostgreSQL.
- `init_db()` ejecuta correctamente.
- Endpoint de conversaciones responde `200`.
- Dashboard devuelve una fila por cliente.
- Pruebas backend pasan (18 tests).
- Frontend compila.
- Flujo de audio esta cubierto por pruebas.
- Preferencia texto/audio esta cubierta por pruebas.
- Maquina de estados con transiciones validadas.
- Sistema de tools con registro, ejecucion e integracion con Groq.

## Brechas pendientes

- Completar credenciales reales de Twilio y Groq.
- Configurar `TWILIO_WEBHOOK_URL` con ngrok o dominio publico.
- Validar firma de webhook de Twilio.
- Autenticacion y autorizacion del dashboard.
- Rate limiting y endurecimiento de seguridad.
- Despliegue productivo y observabilidad.

## Proximas fases (disponibles para colaboradores)

### Fase 3: RAG (FAQ)

Implementar un sistema de preguntas frecuentes con busqueda semantica.

Archivos a crear en `backend/app/services/rag/`:

- `models.py` — Modelo SQLAlchemy `KnowledgeBase` con campos: id, question, answer, category, keywords (array de texto), is_active.
- `faq_loader.py` — Carga FAQs desde archivo JSON o CSV a la base de datos.
- `retrieval_service.py` — Busqueda por palabras clave + reranking con LLM.
- `embedding_service.py` — Placeholder para futuro pgvector.

Endpoints a crear en dashboard:

- `POST /api/dashboard/faq/upload` — subir archivo JSON con FAQs.
- `GET /api/dashboard/faq` — listar FAQs.
- `DELETE /api/dashboard/faq/{id}` — eliminar FAQ.

Flujo de integracion:

1. Usuario pregunta algo sobre politicas/terminos.
2. `retrieval_service.py` busca por keywords en la tabla `knowledge_base`.
3. Obtiene top 5 candidatos y envia a Groq para reranking.
4. Resultado mas relevante se inyecta como contexto en `ResponseGenerator`.

### Fase 4: Mejora de sesiones

- Timeouts y limpieza de sesiones expiradas (cron o tarea programada).
- `restore_session()` en `ConversationRepository` para reanudar sesiones interrumpidas.
- Timeout configurable en `ConversationManager`.

### Fase 5: Frontend (Dashboard)

- Pagina de administracion de FAQs en React.
- `frontend/src/services/faq.service.ts` — cliente HTTP para CRUD de FAQs.
- `frontend/src/hooks/useFaqs.ts` — hook React Query para FAQs.
- Mostrar uso de tools en la vista de conversacion (tool calls ejecutados por el bot).

## Notas para nuevos colaboradores

- Para agregar una tool: crear funcion con decorador `@tool()` en `backend/app/services/tools/` y asegurar que se importe en el startup de la app o en `AIOrchestrator`.
- Las tools que requieren DB deben tener `requires_db=True` y recibir `db` como parametro. El `ToolExecutor` inyecta la sesion automaticamente.
- La maquina de estados valida transiciones en runtime. Si una transicion no es valida, el sistema lanza `ValueError`. Revisar `transitions.py` para ver las reglas.
- Los tests se ejecutan con `pytest backend/tests/ -v` desde la carpeta `backend/`.
