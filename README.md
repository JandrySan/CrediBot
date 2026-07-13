# CrediBot

Asistente de precalificacion de creditos por WhatsApp.

Actualizado: 2026-07-12

## Estado actual

CrediBot es un MVP funcional que automatiza la primera atencion de solicitudes de credito por WhatsApp. El sistema recibe mensajes de clientes, procesa texto o audio, extrae datos con IA, aplica reglas de negocio controladas por codigo, guarda la informacion en PostgreSQL y permite que un asesor humano intervenga desde un dashboard.

Componentes principales:

- Backend con FastAPI + SQLAlchemy.
- Base de datos PostgreSQL.
- Frontend con React + TypeScript + MUI.
- Integracion WhatsApp mediante Twilio Sandbox.
- IA con Groq para intencion, extraccion de datos y apoyo conversacional controlado.
- FAQ/RAG basico para responder preguntas de politicas, requisitos y condiciones.
- Transcripcion de audio de WhatsApp a texto.
- Respuesta del bot por texto, o por nota de voz cuando `AUDIO_REPLY_ENABLED=true`.
- Dashboard de asesor con WebSocket para actualizacion en tiempo real.

## Funcionalidades

1. Recepcion de mensajes de WhatsApp en `POST /webhook/whatsapp`.
2. Recepcion y transcripcion de audios enviados por WhatsApp.
3. Conversacion automatica para capturar datos minimos de credito.
4. Extraccion de datos con IA: nombre, monto, plazo e ingresos.
5. Motor de reglas para resultado preliminar.
6. Persistencia de clientes, conversaciones, mensajes, solicitudes, analisis IA e historial de estados.
7. Generacion opcional de notas de voz en formato OGG/Opus.
8. Exposicion publica de audios generados en `GET /webhook/audio/{filename}`.
9. Handoff a asesor humano cuando el cliente lo solicita.
10. Dashboard para ver conversaciones, mensajes y datos de solicitud.
11. Respuesta del asesor desde dashboard hacia WhatsApp.
12. WebSocket para notificar eventos al dashboard en tiempo real.
13. Cierre manual de conversaciones en estado `HANDOFF`.
14. Carga, listado, eliminacion logica y recuperacion de FAQs desde dashboard.
15. Timeout configurable, restauracion y limpieza de sesiones de conversacion.
16. Administracion frontend de FAQs y navegacion interna con React Router.

## Flujo principal

```text
Cliente WhatsApp
  -> Twilio Sandbox
  -> Webhook FastAPI
  -> Orquestador de conversacion
  -> IA para intencion/extraccion
  -> Motor de reglas
  -> PostgreSQL
  -> Respuesta por WhatsApp
  -> Dashboard asesor
```

## Flujo funcional

1. Twilio envia el mensaje al webhook `POST /webhook/whatsapp`.
2. El backend normaliza el telefono y obtiene o crea el cliente.
3. Se obtiene o crea una conversacion abierta.
4. Se obtiene o crea la solicitud de credito vigente.
5. Si el mensaje trae audio, se descarga y se transcribe.
6. Se guarda el mensaje inbound como `TEXT` o `AUDIO`.
7. La IA clasifica intencion y extrae datos.
8. El sistema guarda los datos extraidos en cliente o solicitud.
9. Si faltan datos, se pregunta el siguiente campo requerido.
10. Si ya estan completos los datos, se aplica el motor de reglas.
11. Se guarda la respuesta outbound.
12. El bot responde por texto; si `AUDIO_REPLY_ENABLED=true`, intenta responder con audio y cae a texto si falla.
13. Se emite un evento WebSocket para actualizar el dashboard.

## Estados de conversacion

Los estados estan definidos en `backend/app/state_machine/states.py`:

- `START`
- `ASK_NAME`
- `ASK_AMOUNT`
- `ASK_TERM`
- `ASK_INCOME`
- `SHOW_RESULT`
- `HANDOFF`
- `END`

## Reglas de negocio

Las reglas estan en `backend/app/services/rules/credit_rule_engine.py`.

Reglas actuales:

- Si `monthly_income < 600` -> `OBSERVADO`.
- Si `amount > monthly_income * 8` -> `OBSERVADO`.
- Si `term_months > 60` -> `OBSERVADO`.
- Caso contrario -> `PREAPROBADO`.

Punto importante: la IA no decide libremente el resultado del credito. La IA ayuda a interpretar mensajes y extraer datos, pero la decision final se calcula mediante reglas explicitas y auditables.

## IA

Servicios principales:

- `backend/app/services/ai/ai_gateway.py`: cliente central para Groq.
- `backend/app/services/ai/ai_orchestrator.py`: coordina intencion, extraccion y respuestas.
- `backend/app/services/ai/intent_detector.py`: clasifica intencion.
- `backend/app/services/ai/entity_extractor.py`: extrae datos de credito.
- `backend/app/services/ai/response_generator.py`: pule respuestas sin cambiar datos ni reglas.
- `backend/app/services/rag/retrieval_service.py`: busca FAQs por palabras clave y reranking opcional con Groq.

## FAQ/RAG

La Fase 3 esta implementada en `backend/app/services/rag/`.

Componentes:

- `models.py`: modelo SQLAlchemy `KnowledgeBase`.
- `faq_loader.py`: carga FAQs desde JSON o CSV.
- `retrieval_service.py`: busqueda por palabras clave y reranking opcional con Groq.
- `embedding_service.py`: placeholder para una futura integracion con embeddings/pgvector.

El flujo actual usa FAQs para preguntas sobre requisitos, documentos, tasas, politicas, condiciones y temas similares. En modo conversacional, el contexto FAQ se agrega al prompt de IA. En el flujo estructurado, si el usuario hace una pregunta de politica con una FAQ relevante, el bot responde esa FAQ y luego ofrece continuar con la precalificacion.

Frontend:

- Ruta `/faqs` con pantalla de administracion.
- `frontend/src/services/faq.service.ts`: cliente HTTP para listar, cargar y eliminar FAQs.
- `frontend/src/hooks/useFaqs.ts`: hooks React Query para listado, upload y eliminacion.
- `frontend/src/pages/FaqAdminPage.tsx`: carga JSON/CSV, lista FAQs activas y elimina FAQs de forma logica.

Formato JSON aceptado por upload:

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

Modo de operacion:

```env
AI_ONLY_MODE=false
```

Con `false`, el sistema usa el flujo de negocio completo con estados y reglas. Con `true`, responde de forma conversacional con IA sin aplicar reglas de negocio. Para el MVP de precalificacion, el modo recomendado es `false`.

## Audio

CrediBot soporta audio en dos direcciones:

### Cliente envia audio

- El webhook detecta media de tipo audio.
- `SpeechToTextService` descarga el archivo desde Twilio.
- Se transcribe con Groq STT o modelo local.
- El texto transcrito entra al mismo flujo de negocio.

### Bot responde audio

- `TextToSpeechService` genera un MP3 con gTTS.
- Luego lo convierte a OGG/Opus.
- Twilio descarga el archivo desde `GET /webhook/audio/{filename}`.
- Si falla la generacion de audio, el bot responde en texto.
- Estado actual: la respuesta en audio se controla de forma global con `AUDIO_REPLY_ENABLED`.

### Preferencia por cliente

Pendiente de implementacion.

La documentacion anterior mencionaba `customers.preferred_response_type`, pero el modelo `Customer` actual no tiene ese campo y el webhook no interpreta frases como "respondeme en audio" o "solo texto" para cambiar una preferencia por cliente.

## Dashboard del asesor

Frontend ubicado en `frontend/src`.

Funcionalidades:

- Ver estadisticas generales.
- Listar conversaciones.
- Ver mensajes de una conversacion.
- Ver datos de credito del cliente.
- Tomar una conversacion como asesor.
- Responder al cliente por WhatsApp.
- Cerrar una conversacion en `HANDOFF`.
- Ejecutar limpieza manual de conversaciones abiertas expiradas.
- Administrar FAQs desde la ruta `/faqs`.

La app usa `react-router-dom` para navegar entre el panel principal (`/`) y FAQs (`/faqs`).

Estado actual: `GET /api/dashboard/conversations` lista conversaciones unidas con solicitudes de credito. Si un cliente tiene varias conversaciones o solicitudes, puede devolver mas de una fila para ese cliente. La deduplicacion por cliente queda pendiente.

## Respuesta del asesor por WhatsApp

Endpoint:

```text
POST /api/dashboard/conversations/{id}/reply
```

Flujo:

1. El asesor escribe desde el dashboard.
2. El backend obtiene el cliente y telefono.
3. El backend guarda el mensaje como `OUTBOUND`.
4. `TwilioWhatsAppService` intenta enviar el mensaje por WhatsApp.
5. Si Twilio falla, el endpoint devuelve `success=false`, pero el mensaje ya quedo guardado en la base de datos.

Pendiente: cambiar el orden para guardar el mensaje solo despues de confirmar envio exitoso, o guardar un estado explicito de fallo.

## Base de datos

Base principal: PostgreSQL.

Modelos principales:

- `Customer`
- `Conversation`
- `Message`
- `CreditApplication`
- `AIAnalysis`
- `ConversationStateHistory`

Nota: el campo `customers.preferred_response_type` esta pendiente. No existe en el modelo actual ni en la inicializacion de base de datos.

## Sesiones de conversacion

La Fase 4 esta implementada con timeout configurable y limpieza de sesiones abiertas.

Variables:

```env
CONVERSATION_SESSION_TIMEOUT_MINUTES=60
CONVERSATION_CLEANUP_BATCH_SIZE=100
```

Comportamiento:

- `ConversationRepository.get_or_create_active()` reutiliza una conversacion abierta si no expiro.
- Si la conversacion abierta expiro, se marca como `CLOSED`, pasa a estado `END`, guarda resultado `EXPIRADO` y se crea una nueva conversacion `ACTIVE`.
- `ConversationRepository.restore_session()` devuelve una sesion abierta solo si existe y no expiro.
- `ConversationManager.cleanup_expired_sessions()` cierra sesiones abiertas vencidas por lotes.
- El startup ejecuta una limpieza inicial.
- `MessageRepository.save_message()` actualiza `conversations.updated_at` para reflejar actividad reciente.

Configuracion por defecto:

```env
DATABASE_URL=
DB_HOST=localhost
DB_PORT=5432
DB_NAME=credibot
DB_USER=postgres
DB_PASSWORD=12345678
```

Si `DATABASE_URL` esta vacio, el sistema construye la URL PostgreSQL con las variables `DB_*`.

## Variables de entorno

Archivo usado por el backend:

```text
backend/.env
```

Archivo de referencia:

```text
backend/.env.example
```

Variables principales:

```env
# DB
DATABASE_URL=
DB_HOST=localhost
DB_PORT=5432
DB_NAME=credibot
DB_USER=postgres
DB_PASSWORD=12345678

# IA
GROQ_API_KEY=tu_groq_api_key
AI_ONLY_MODE=false

# Audio STT
AUDIO_STT_ENABLED=true
AUDIO_STT_PROVIDER=groq
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
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
TWILIO_WHATSAPP_NUMBER=+14155238886
TWILIO_WEBHOOK_URL=https://tu-ngrok/webhook/whatsapp
```

Notas:

- `TWILIO_ACCOUNT_SID` debe empezar con `AC`.
- No usar un SID de API Key que empieza con `SK`.
- Para audio, `TWILIO_WEBHOOK_URL` debe ser publico porque Twilio necesita descargar el archivo OGG.
- Si `AUDIO_REPLY_PUBLIC_BASE_URL` queda vacio, se deriva desde `TWILIO_WEBHOOK_URL`.

## Ejecucion local

Backend:

```powershell
cd backend
.\.venv\Scripts\python.exe -m uvicorn main:app --host 0.0.0.0 --port 8000
```

Frontend:

```powershell
cd frontend
npm run dev
```

## CI/CD y despliegue AWS

El repositorio incluye workflows de GitHub Actions para:

- Validar backend FastAPI con instalacion, verificacion de sintaxis y pruebas.
- Validar frontend React con lint y build.
- Publicar la imagen Docker del backend en Amazon ECR.
- Actualizar un servicio ECS Fargate existente usando OIDC, sin access keys estaticas.

Documentacion completa: `docs/despliegue-aws.md`.

Variables principales para GitHub Actions:

```text
AWS_REGION
AWS_ECR_REPOSITORY
AWS_ROLE_ARN
AWS_ECS_CLUSTER
AWS_ECS_SERVICE
AWS_ECS_CONTAINER_NAME (opcional si la task tiene un solo contenedor)
```

Variables principales para el backend en ECS:

```text
DATABASE_URL
SUPABASE_DATABASE_URL
GROQ_API_KEY
TWILIO_ACCOUNT_SID
TWILIO_AUTH_TOKEN
TWILIO_WHATSAPP_FROM
TWILIO_WHATSAPP_NUMBER
TWILIO_WEBHOOK_URL
BACKEND_CORS_ORIGINS
```

El frontend web ya no tiene la API fija a localhost. Para local o produccion, usar:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
VITE_WS_BASE_URL=ws://127.0.0.1:8000
```

En produccion, apuntar esas variables a la URL HTTPS final del backend.

## Prueba con Twilio Sandbox

1. Levantar backend en puerto `8000`.
2. Exponer backend con ngrok:

```powershell
ngrok http 8000
```

3. Configurar en Twilio Sandbox:

```text
When a message comes in: https://<ngrok>/webhook/whatsapp
Metodo: POST
```

4. Completar en `backend/.env`:

```env
TWILIO_WEBHOOK_URL=https://<ngrok>/webhook/whatsapp
```

5. Unir el numero al Sandbox con el codigo `join ...`.
6. Enviar mensajes por WhatsApp.

## Endpoints

### Salud

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
- `POST /api/dashboard/faq/upload`
- `GET /api/dashboard/faq`
- `DELETE /api/dashboard/faq/{id}`

### WebSocket

- `GET ws://<host>/ws/dashboard`

## Validacion realizada

- Backend conecta con PostgreSQL.
- Inicializacion de tablas ejecutada.
- Build frontend pasa con `npm run build`.
- Pruebas backend pasan con `DEBUG=false` inyectado en el entorno: `23 passed`.
- Flujo de audio cubierto por pruebas.
- Envio del asesor por Twilio validado a nivel de servicio.
- FAQ/RAG cubierto por pruebas unitarias de carga y busqueda.
- Sesiones de conversacion cubiertas por pruebas de restauracion, expiracion y limpieza.
- Frontend de FAQs compila con `npm run build`.

Estado de pruebas backend:

- Las pruebas no corren actualmente si `backend/.env` contiene `DEBUG=release`, porque `settings.DEBUG` es booleano y Pydantic no puede interpretar `release`.
- Para ejecutar pruebas, usar un valor booleano valido como `DEBUG=false` o aislar la configuracion de test.

## Pendientes

- Completar credenciales reales de Twilio y Groq en `backend/.env`.
- Configurar URL publica con ngrok o dominio.
- Corregir `DEBUG` en `backend/.env` para que sea booleano.
- Implementar o retirar de la documentacion la preferencia por cliente para texto/audio.
- Alinear el guardado de respuestas del asesor con el resultado real de Twilio.
- Cargar automaticamente las tools (`financial_tools`, `customer_tools`, `policy_tools`) y corregir el ciclo de tool calling.
- Deduplicar conversaciones por cliente en el dashboard si ese sigue siendo el comportamiento deseado.
- Validar firma de webhook de Twilio.
- Agregar autenticacion y roles al dashboard.
- Agregar rate limiting y politicas de seguridad.
- Preparar despliegue productivo.
