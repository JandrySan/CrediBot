
# CrediBot - Estado del Proyecto

## Información General

**Nombre del proyecto:** CrediBot

**Objetivo:**

CrediBot es un asistente inteligente para la precalificación de créditos mediante WhatsApp. El sistema utiliza Inteligencia Artificial para mantener conversaciones con los clientes, recopilar información financiera, evaluar reglas de negocio y permitir la intervención de un asesor humano cuando sea necesario.

---

# Arquitectura

El proyecto está dividido en dos grandes módulos:

```
CrediBot
│
├── backend (FastAPI)
│
├── frontend (React + TypeScript)
│
└── PostgreSQL
```

Tecnologías utilizadas:

- FastAPI
- SQLAlchemy
- PostgreSQL
- React
- TypeScript
- Material UI
- React Query
- WebSockets
- Groq API (IA)
- Twilio WhatsApp (✅ integrado)
- Ngrok (para tunneling local)

---

# Backend implementado

## Base de datos

Se encuentran implementadas las siguientes entidades:

- Customer
- Conversation
- Message
- CreditApplication
- AIAnalysis
- ConversationStateHistory

---

## Máquina de estados

Estados implementados:

- START
- ASK_NAME
- ASK_AMOUNT
- ASK_TERM
- ASK_INCOME
- SHOW_RESULT
- HANDOFF

La conversación cambia automáticamente de estado según la información recopilada.

---

## Inteligencia Artificial

Implementado:

- Análisis de intención
- Extracción de datos
- Mejora de respuestas
- Clasificación de mensajes

Actualmente se utiliza:

Groq API

---

## Reglas de negocio

Se implementó un motor de precalificación.

Actualmente valida:

- monto solicitado
- plazo
- ingresos mensuales

Resultados posibles:

- PREAPROBADO
- OBSERVADO

---

## Persistencia

Se almacenan:

Clientes

Conversaciones

Mensajes

Análisis de IA

Resultados del crédito

Historial de estados

---

## Dashboard API

Endpoints implementados

GET

```
/api/dashboard/stats
```

Obtiene estadísticas generales.

---

GET

```
/api/dashboard/conversations
```

Lista conversaciones.

---

GET

```
/api/dashboard/conversations/{id}/messages
```

Obtiene el historial del chat.

---

POST

```
/api/dashboard/conversations/{id}/take
```

Permite que un asesor tome la conversación.

---

POST

```
/api/dashboard/conversations/{id}/reply
```

Permite responder desde el panel del asesor.

- Guarda el mensaje en la base de datos
- Envía el mensaje a través de Twilio WhatsApp
- Actualiza el chat en tiempo real para el cliente y el asesor

---

## Integración Twilio

✅ **Estado: Implementada y funcionando**

### Webhook de entrada
- **Endpoint:** POST /webhook/whatsapp
- **Recibe:** Mensajes de WhatsApp desde Twilio
- **Procesa:** El mensaje a través del orquestador de conversación
- **Responde:** Con TwiML válido para Twilio

### Servicio de envío
- **Normalización:** Convierte números al formato E.164 (ej: +3001234567)
- **Fallback:** Soporta tanto TWILIO_WHATSAPP_FROM como TWILIO_WHATSAPP_NUMBER
- **Manejo de errores:** Captura excepciones de Twilio sin romper el flujo

### Configuración requerida
Las siguientes variables deben estar en `.env`:
- TWILIO_ENABLED=true
- TWILIO_ACCOUNT_SID=tu_sid
- TWILIO_AUTH_TOKEN=tu_token
- TWILIO_WHATSAPP_FROM=whatsapp:+1415XXXXXXX
- TWILIO_WHATSAPP_NUMBER=+1415XXXXXXX
- TWILIO_WEBHOOK_URL=https://tu-tunel/webhook/whatsapp

---

# Frontend implementado

Framework

React + TypeScript

---

## Dashboard

Implementado

✔ Estadísticas

✔ Conversaciones

✔ Chat

✔ Información del cliente

✔ Respuesta del asesor

✔ Tomar conversación

---

## Componentes

Layout

Sidebar

TopBar

Dashboard

---

Conversaciones

ConversationList

ConversationItem

ConversationChat

ConversationInfoPanel

ReplyBox

---

Hooks

useDashboard

useConversations

useConversationMessages

useDashboardSocket

useTakeConversation

useReplyConversation

---

Servicios

conversation.service.ts

dashboard.service.ts

---

# Funcionalidades implementadas

✔ Recepción de mensajes

✔ Conversación mediante IA

✔ Extracción automática de datos

✔ Persistencia

✔ Precalificación

✔ Dashboard administrativo

✔ Chat estilo WhatsApp

✔ Información del cliente

✔ Derivación a asesor

✔ Respuesta manual desde el panel

✔ WebSockets

✔ Actualización en tiempo real

---

# Diseño

Actualmente se mejoró:

- Theme
- Sidebar
- Dashboard
- Cards
- Lista de conversaciones

Pendiente:

- mejorar Chat
- mejorar panel derecho
- modo oscuro

---

# Estado actual

Backend

90 %

Frontend

75 %

IA

90 %

Dashboard

85 %

Tiempo real

100 %

---

# Pendiente

## Integración WhatsApp

Pendiente configurar:

Twilio Sandbox

Ngrok

Webhook

Variables de entorno

Envío real de mensajes

---

## Audio

Pendiente

Recepción

Transcripción

Respuesta mediante voz

---

## Analítica

Pendiente

Gráficas

Indicadores

Reportes

Embudo

---

## Exportaciones

Pendiente

PDF

Excel

CSV

---

## Seguridad

Pendiente

Login

Roles

JWT

Administradores

Asesores

---

## Producción

Pendiente

Docker

Render / Railway

Dominio

HTTPS

---

# Flujo completo del sistema

Cliente

↓

WhatsApp

↓

Webhook FastAPI

↓

IA (Groq)

↓

Extracción de datos

↓

Reglas de negocio

↓

Resultado

↓

Dashboard

↓

Asesor (si es necesario)

↓

Respuesta manual

↓

WhatsApp (pendiente Twilio)

---

# Integración Twilio (pendiente)

Se encuentra implementado el servicio:

```
TwilioWhatsAppService
```

Falta únicamente:

- configurar credenciales

- configurar Sandbox

- configurar Ngrok

- cambiar webhook

- realizar pruebas finales

---

# Observaciones

Actualmente el proyecto se encuentra completamente funcional para pruebas locales.

La única integración pendiente para disponer del flujo completo es la conexión entre el Dashboard y WhatsApp mediante Twilio Sandbox.

Una vez realizada esta integración, el sistema permitirá:

- recibir mensajes reales desde WhatsApp

- responder automáticamente mediante IA

- derivar conversaciones

- responder manualmente desde el panel administrativo

- mantener el historial completo de la conversación

---

# Estado General

Proyecto estable.

El núcleo del sistema está desarrollado.

El trabajo pendiente corresponde principalmente a integraciones externas, mejoras visuales y funcionalidades complementarias.