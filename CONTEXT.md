# CrediBot - Contexto del Proyecto

## 📋 Resumen Ejecutivo

**CrediBot** es un asistente inteligente de precalificación de créditos que opera a través de WhatsApp. Utiliza IA para conducir conversaciones naturales con clientes, recopila información financiera automáticamente y evalúa reglas de negocio para proporcionar resultados de precalificación. Los asesores humanos pueden intervenir en cualquier momento a través de un dashboard administrativo.

---

## 🎯 Objetivos Principales

1. **Automatizar precalificación**: Reduce el tiempo de evaluación inicial de créditos mediante IA
2. **Mejorar experiencia del cliente**: Interacción natural a través de WhatsApp
3. **Facilitar derivación**: Paso fluido a asesores humanos cuando sea necesario
4. **Generar datos**: Registra historial de conversaciones y análisis de IA para auditoría y mejora

---

## 🏗️ Arquitectura del Proyecto

```
CrediBot/
├── backend/              # FastAPI + SQLAlchemy
│   ├── app/
│   │   ├── api/         # Routers (webhooks, dashboard, websocket)
│   │   ├── config/      # Configuración y variables de entorno
│   │   ├── database/    # Sesiones y inicialización DB
│   │   ├── models/      # Modelos SQLAlchemy
│   │   ├── repositories/  # Acceso a datos
│   │   ├── services/    # Lógica de negocio
│   │   │   ├── ai/      # Orquestación de IA (Groq)
│   │   │   ├── conversation/  # Máquina de estados
│   │   │   ├── tools/   # Sistema de Tools / Function Calling
│   │   │   ├── rag/     # RAG (FAQs, búsqueda semántica)
│   │   │   ├── audio/   # Procesamiento de audio (STT)
│   │   │   ├── whatsapp/  # Integración Twilio
│   │   │   └── websocket/  # Conexiones en tiempo real
│   │   └── state_machine/  # Definición de estados
│   ├── main.py          # Aplicación FastAPI
│   ├── requirements.txt  # Dependencias
│   ├── .env            # Variables de entorno
│   └── tests/          # Pruebas unitarias
│
├── frontend/            # React + TypeScript + Vite
│   ├── src/
│   │   ├── components/  # Componentes React
│   │   ├── hooks/       # Custom hooks
│   │   ├── pages/       # Páginas
│   │   ├── services/    # Servicios HTTP/WS
│   │   ├── types/       # Tipos TypeScript
│   │   ├── theme/       # Tema Material UI
│   │   ├── api/         # Configuración Axios
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── vite.config.ts
│   ├── tsconfig.json
│   └── package.json
│
└── README.md            # Documentación general
```

---

## 🗄️ Modelo de Datos

### Entidades Principales

```
Customer
├── id (PK)
├── phone_number (único)
├── full_name
└── created_at

Conversation
├── id (PK)
├── customer_id (FK)
├── current_state
├── status (ACTIVE, HANDOFF, COMPLETED)
├── result
└── created_at

Message
├── id (PK)
├── conversation_id (FK)
├── direction (INBOUND, OUTBOUND)
├── message_type (TEXT, AUDIO, etc)
├── content
└── created_at

CreditApplication
├── id (PK)
├── customer_id (FK)
├── amount
├── term_months
├── monthly_income
├── result (PREAPROBADO, OBSERVADO)
├── reason
└── created_at

AIAnalysis
├── id (PK)
├── conversation_id (FK)
├── intent
├── extracted_data (JSON)
├── model_used
└── created_at

ConversationStateHistory
├── id (PK)
├── conversation_id (FK)
├── previous_state
├── new_state
├── reason
└── created_at

DocumentChunk
├── id (PK)
├── content (texto del chunk)
├── embedding (vector 384-dim serializado)
├── source_info (JSON: sección, pregunta)
└── created_at
```

---

## 🔄 Flujo de Conversación

### Estados de la Máquina

```
START
  ↓
ASK_NAME (¿Nombre completo?)
  ↓
ASK_AMOUNT (¿Cuánto dinero?)
  ↓
ASK_TERM (¿A cuántos meses?)
  ↓
ASK_INCOME (¿Ingresos mensuales?)
  ↓
SHOW_RESULT (Resultado: PREAPROBADO o OBSERVADO)
  ↓
HANDOFF (Usuario solicita asesor)
```

### Flujo de Procesamiento de Mensaje

1. **Recepción (Webhook Twilio)**
   - POST /webhook/whatsapp
   - Twilio envía: From, Body, ProfileName, MediaUrl0 (para audio)

2. **Orquestación**
   - ConversationOrchestrator.handle_text_message()
   - Obtiene o crea Customer
   - Obtiene o crea Conversation activa
   - Obtiene o crea CreditApplication

3. **Análisis de IA**
   - AIOrchestrator analiza el mensaje
   - Extrae intent, nombre, monto, plazo, ingresos

4. **Aplicación de Datos**
   - Actualiza Customer con datos extraídos
   - Actualiza CreditApplication con datos

5. **Evaluación**
   - CreditRuleEngine evalúa si la solicitud es completa
   - Si es completa, evalúa reglas de negocio
   - Retorna PREAPROBADO o OBSERVADO

6. **Transición de Estado**
   - Cambia el estado de Conversation si corresponde
   - Registra la transición en ConversationStateHistory

7. **Enriquecimiento con Tools** (nuevo)
   - _enrich_with_tools() ejecuta el ciclo de function calling
   - La IA puede invocar tools: search_faqs, calculate_monthly_payment, handoff_to_agent
   - El resultado de las tools se retroalimenta al modelo para generar la respuesta final

8. **Generación de Respuesta**
   - AIOrchestrator mejora la respuesta con ResponseImprover
   - Guarda el mensaje OUTBOUND
   - Retorna el mensaje al webhook de Twilio

9. **Transmisión en Tiempo Real**
   - Broadcast via WebSocket al dashboard
   - Dashboard se actualiza sin refresh

---

## 🤖 Integración de IA (Groq)

### Componentes Originales

- **IntentDetector**: Identifica si el usuario quiere hablar con un asesor
- **EntityExtractor**: Extrae datos (nombre, monto, plazo, ingresos)
- **ResponseGenerator**: Genera respuestas contextuales
- **ResponseImprover**: Mejora la calidad de respuestas

### Function Calling (Tool System)

El AIGateway ahora soporta function calling nativo de Groq. El flujo extendido es:

```
Mensaje → IntentDetector → (intent)
       → EntityExtractor → {full_name, amount, term_months, monthly_income}
       → [Evaluación + Reglas de Negocio]
       → ResponseGenerator → Respuesta base
       → _enrich_with_tools():
          │  Groq recibe: respuesta base + tools disponibles
          │  ├─ search_faqs(query) → FAQ relevante
          │  ├─ check_credit_rules(amount, term, income) → PREAPROBADO/OBSERVADO
          │  ├─ calculate_monthly_payment(amount, term, rate) → cuota mensual
          │  └─ handoff_to_agent(reason) → deriva a asesor
          │  El resultado de la tool vuelve al modelo → respuesta enriquecida
       → ResponseImprover → Respuesta mejorada final
```

---

## 🧰 Sistema de Tools

**Ubicación**: `app/services/tools/`

### Arquitectura

```
Tool (ABC)
├── name: str
├── description: str (para que la IA decida cuándo usarla)
├── parameters: dict (JSON Schema de argumentos)
├── run(**kwargs) → ejecuta la herramienta
└── to_definition() → formato Groq/OpenAI function calling

ToolRegistry
├── register(tool)
├── get(name)
├── get_all()
└── list_definitions()

ToolExecutor
└── execute(system_prompt, messages, available_tools, max_rounds=5)
    ├── Llama a Groq con tools definidas
    ├── Si Groq retorna tool_calls → ejecuta cada tool
    ├── Retroalimenta el resultado a Groq
    └── Retorna respuesta final con contexto de tools
```

### Tools Disponibles

| Tool | Disparo (cuándo la IA la usa) | Parámetros |
|------|-------------------------------|------------|
| `check_credit_rules` | El usuario proporciona monto, plazo e ingresos | amount, term_months, monthly_income |
| `calculate_monthly_payment` | El usuario pregunta cuánto pagaría al mes | amount, term_months, annual_rate |
| `handoff_to_agent` | El usuario solicita un asesor o muestra insatisfacción | reason |
| `search_faqs` | El usuario pregunta sobre tasas, requisitos, políticas | query |

Las tools se registran automáticamente al iniciar el módulo `app/services/tools/__init__.py`. La tool `search_faqs` se registra dinámicamente cuando el orquestador detecta que la base de conocimiento tiene datos.

---

## 📚 RAG (Búsqueda Semántica en FAQs)

**Ubicación**: `app/services/rag/`

### Arquitectura

```
EmbeddingService
├── Modelo: all-MiniLM-L6-v2 (384 dimensiones)
├── embed(text) → vector
└── embed_batch(texts) → vectores

VectorStore
├── insert_chunks(chunks) → almacena texto + embedding + metadatos
├── search(query_embedding, top_k) → búsqueda por similitud coseno
└── Soporte: pgvector (PostgreSQL) o cómputo en Python

Retriever
├── search(query, top_k) → embed → vector_store.search → resultados
└── format_context(results, max_chars) → texto plano para el LLM

KnowledgeBase
├── ingest_faq_file(file_path) → carga markdown → chunking → embed → store
├── query(question) → retrieve → format_context
└── is_ready() → verifica si hay datos indexados
```

### Ingestión de FAQs

El archivo fuente está en `app/services/rag/data/faqs.md`. Para indexarlo:

```bash
cd backend
python -c "
from app.database.session import SessionLocal
from app.services.rag.knowledge_base import KnowledgeBase

db = SessionLocal()
kb = KnowledgeBase(db)
kb.ingest_faq_file('app/services/rag/data/faqs.md')
print('FAQs indexadas correctamente')
"
```

### Formato del FAQ

El archivo FAQs.md usa markdown con secciones (`#`) y preguntas (`##`):

```markdown
# Nombre de Sección

## ¿Pregunta?
Respuesta en texto plano.
```

Cada pregunta/respuesta se convierte en un chunk independiente con metadatos de sección y pregunta.

---

## 🔊 Procesamiento de Audio

**Ubicación**: `app/services/audio/speech_to_text.py`

### SpeechToTextService

- Usa `faster-whisper` (modelo `base`) para transcripción
- Soporta descarga desde URL (MediaUrl0 de Twilio) o archivos locales
- Formatos soportados: OGG, MP3, WAV, M4A

### Flujo

```
Twilio envía mensaje con MediaUrl0 (audio)
    ↓
Webhook detecta media_type "audio" → llama a transcribe_url()
    ↓
Descarga el audio → faster-whisper → texto transcrito
    ↓
El texto se procesa como un mensaje normal (handle_text_message)
```

---

## 💬 Integración Twilio WhatsApp

### Arquitectura

```
WhatsApp (Usuario)
    ↓
Twilio Cloud
    ↓ (POST)
https://strep-aging-angler.ngrok-free.dev/webhook/whatsapp
    ↓
FastAPI → ConversationOrchestrator
    ↓ (TwiML XML)
Twilio
    ↓
WhatsApp (Respuesta)
```

### Endpoints

| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | /webhook/whatsapp | Recibe mensajes de Twilio (texto y audio) |

### Soporte de Audio

El webhook ahora acepta los parámetros adicionales:
- `MediaUrl0`: URL del archivo de audio enviado por el usuario
- `MediaContentType0`: tipo MIME del media (ej: audio/ogg)

Cuando se recibe un audio, se transcribe automáticamente con SpeechToTextService y se procesa como un mensaje de texto.

### Servicio Twilio

**Archivo**: `app/services/whatsapp/twilio_service.py`

```python
TwilioWhatsAppService
├── send_message(to, body)
│   ├── Normaliza números (E.164)
│   ├── Maneja fallback de configuración
│   └── Captura excepciones TwilioRestException
├── _normalize_phone_number(phone)
│   ├── Soporta formatos: +XX, 00XX, XX
│   └── Retorna E.164
└── _get_from_number()
    ├── Fallback: TWILIO_WHATSAPP_FROM → TWILIO_WHATSAPP_NUMBER
    └── Retorna número de WhatsApp
```

### Flujo de Envío de Mensajes

1. **Desde el bot**: Automáticamente después de procesar mensajes del usuario
2. **Desde el asesor**: POST /api/dashboard/conversations/{id}/reply
   - Guarda en BD
   - Envía con TwilioWhatsAppService
   - Broadcast a WebSocket

### Configuración

**Variables requeridas en `.env`**:

```env
# Twilio
TWILIO_ENABLED=true
TWILIO_ACCOUNT_SID=tu_account_sid
TWILIO_AUTH_TOKEN=tu_auth_token
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
TWILIO_WHATSAPP_NUMBER=+14155238886
TWILIO_WEBHOOK_URL=https://tu-tunel.ngrok-free.app/webhook/whatsapp
```

### Prueba Local con Ngrok

```bash
# Terminal 1: Inicia ngrok
ngrok http 8000

# Terminal 2: Inicia backend
cd backend
.\.venv\Scripts\python -m uvicorn main:app --host 0.0.0.0 --port 8000

# Consola de Twilio: Configura el webhook
# Webhook URL: https://[ngrok-url]/webhook/whatsapp
```

---

## 📊 Dashboard API

### Autenticación
Actualmente sin autenticación. Pendiente: implementar JWT.

### Endpoints

#### Estadísticas
```http
GET /api/dashboard/stats
```
Retorna:
- customers: Total de clientes
- conversations: Total de conversaciones
- active_conversations: Conversaciones activas
- handoff_conversations: Derivadas a asesores
- preapproved: Créditos preaprobados
- observed: Créditos en revisión

#### Conversaciones
```http
GET /api/dashboard/conversations
```
Retorna lista con:
- conversation_id, customer_id, phone_number, full_name
- state, status, result
- credit_amount, term_months, monthly_income
- created_at

#### Mensajes de Conversación
```http
GET /api/dashboard/conversations/{id}/messages
```
Retorna:
- id, direction (INBOUND/OUTBOUND), type, content, created_at

#### Tomar Conversación
```http
POST /api/dashboard/conversations/{id}/take
```
Cambia status a HANDOFF, state a HANDOFF

#### Responder del Asesor
```http
POST /api/dashboard/conversations/{id}/reply
Content-Type: application/x-www-form-urlencoded

message=Tu+respuesta
```
- Guarda mensaje en BD
- Envía por Twilio WhatsApp
- Broadcast por WebSocket

---

## 🎨 Frontend

### Estructura de Componentes

```
App
├── MainLayout
│   ├── Sidebar
│   │   └── Navegación
│   ├── TopBar
│   │   └── Información
│   └── Dashboard
│       ├── DashboardPage
│       │   ├── Estadísticas
│       │   ├── ConversationList
│       │   │   └── ConversationItem (clickeable)
│       │   └── ConversationChat
│       │       ├── ConversationInfoPanel
│       │       └── ReplyBox (para asesores)
```

### Custom Hooks

| Hook | Propósito |
|------|-----------|
| useDashboard | Obtiene estadísticas |
| useConversations | Lista y actualización en tiempo real |
| useConversationMessages | Historial de mensajes |
| useDashboardSocket | Conexión WebSocket |
| useTakeConversation | Tomar conversación |
| useReplyConversation | Enviar respuesta del asesor |

### Servicios HTTP

| Servicio | Métodos |
|----------|---------|
| conversation.service.ts | getConversations, getMessages |
| dashboard.service.ts | getStats, takeConversation, reply |

---

## 🧪 Testing

### Pruebas Unitarias

**Archivos**: `backend/tests/`

Verifica:
- Normalización de números telefónicos
- Uso correcto del número de Twilio
- Respuestas exitosas
- Operaciones de repositorios (customer, conversation)

Ejecutar:
```bash
cd backend
.\.venv\Scripts\python -m pytest -q tests/
```

---

## 🚀 Configuración Local

### Requisitos

- Python 3.10+
- PostgreSQL 12+
- Node.js 18+
- Git

### Backend

```bash
cd backend

# Crear entorno virtual
python -m venv .venv
.\.venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables
cp .env.example .env
# Editar .env con tus credenciales

# Inicializar BD
python -c "from app.database.init_db import init_db; init_db()"

# Ingestar FAQs (opcional, una vez)
python -c "
from app.database.session import SessionLocal
from app.services.rag.knowledge_base import KnowledgeBase
db = SessionLocal()
kb = KnowledgeBase(db)
kb.ingest_faq_file('app/services/rag/data/faqs.md')
print('FAQs indexadas')
"

# Ejecutar
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend

# Instalar dependencias
npm install

# Ejecutar
npm run dev
# Acceder en http://localhost:5173
```

### Ngrok (para Twilio local)

```bash
# Instalar ngrok: https://ngrok.com/download
# O usar WSL

# Exponer puerto 8000
ngrok http 8000

# Copiar la URL y registrar en Twilio
```

---

## 📝 Variables de Entorno

### Backend `.env`

```env
# Base de Datos
DB_HOST=localhost
DB_PORT=5432
DB_NAME=credibot
DB_USER=postgres
DB_PASSWORD=xxxxx

# Twilio
TWILIO_ENABLED=true
TWILIO_ACCOUNT_SID=xxxxx
TWILIO_AUTH_TOKEN=xxxxx
TWILIO_WHATSAPP_FROM=whatsapp:+1415XXXXXXX
TWILIO_WHATSAPP_NUMBER=+1415XXXXXXX
TWILIO_WEBHOOK_URL=https://xxxxx.ngrok-free.app/webhook/whatsapp

# IA
GROQ_API_KEY=xxxxx

# App
APP_NAME=CrediBot
DEBUG=True
```

---

## 🔐 Seguridad (Pendiente)

- [ ] Validación de firma de webhook de Twilio
- [ ] Autenticación JWT en dashboard API
- [ ] Encriptación de datos sensibles en BD
- [ ] Rate limiting en endpoints
- [ ] Validación de entrada en todos los endpoints
- [ ] Logs auditados con timestamps

---

## 🐛 Troubleshooting

### Backend no arranca

```bash
# Verificar que uvicorn está instalado
.\.venv\Scripts\python -m uvicorn main:app

# Si falla, reinstalar dependencias
pip install -r requirements.txt --force-reinstall
```

### WebSocket desconectado

```bash
# Verificar que ngrok está corriendo
ngrok http 8000

# Verificar que el CORS está configurado correctamente en main.py
```

### Twilio no recibe webhook

1. Verificar que ngrok está activo
2. Ir a consola Twilio → WhatsApp Sandbox
3. Buscar "When a message comes in"
4. Configurar URL: `https://[ngrok-url]/webhook/whatsapp`
5. Guardar cambios

### El RAG no encuentra respuestas

```bash
# Verificar que las FAQs están indexadas
python -c "
from app.database.session import SessionLocal
from app.services.rag.knowledge_base import KnowledgeBase
db = SessionLocal()
kb = KnowledgeBase(db)
print(f'Chunks indexados: {kb.vector_store.count()}')
"
```

---

## 📚 Documentación de Referencia

- [Twilio WhatsApp API](https://www.twilio.com/docs/whatsapp/api)
- [FastAPI](https://fastapi.tiangolo.com/)
- [SQLAlchemy](https://docs.sqlalchemy.org/)
- [React](https://react.dev/)
- [TypeScript](https://www.typescriptlang.org/)
- [Groq Function Calling](https://console.groq.com/docs/tool-use)
- [sentence-transformers](https://www.sbert.net/)
- [pgvector](https://github.com/pgvector/pgvector)
- [faster-whisper](https://github.com/SYSTRAN/faster-whisper)

---

## 📅 Historial de Cambios

### v1.1.0 - Tool System, RAG y Audio

- ✅ Tool System: base Tool ABC, ToolRegistry, ToolExecutor con ciclo function-calling
- ✅ Tools: check_credit_rules, calculate_monthly_payment, search_faqs, handoff_to_agent
- ✅ RAG con FAQs: EmbeddingService (sentence-transformers), VectorStore, Retriever, KnowledgeBase
- ✅ FAQ inicial con 14 preguntas/respuestas sobre créditos
- ✅ Speech-to-Text con faster-whisper para mensajes de audio
- ✅ AIGateway actualizado con chat() y soporte de tools/tool_choice
- ✅ AIOrchestrator con process_with_tools() para orquestar tools
- ✅ ConversationOrchestrator con _enrich_with_tools() para respuestas enriquecidas
- ✅ Webhook actualizado para recibir MediaUrl0 (audio desde WhatsApp)
- ✅ Modelo DocumentChunk para almacenamiento de vectores

### v1.0.0 - Integración Twilio Completa
- ✅ Webhook de entrada WhatsApp
- ✅ Servicio de envío con normalización
- ✅ Manejo de errores robusto
- ✅ Fallback de configuración
- ✅ Pruebas unitarias

### v0.9.0 - Pre-release
- Estructura base del proyecto
- Dashboard administrativo
- Máquina de estados
- Integración con Groq

---

## 👥 Equipo

**Proyecto**: CrediBot  
**Estado**: Activo  
**Última actualización**: 2026-07-11

---

## 📞 Soporte

Para reportar bugs o sugerencias, documentar en issues del repositorio con:
- Descripción detallada
- Pasos para reproducir
- Logs relevantes
- Environment info

---
