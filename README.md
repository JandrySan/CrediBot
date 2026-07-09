# CrediBot

Asistente de precalificacion de creditos por WhatsApp.

Actualizado: 2026-07-08

## Estado real del proyecto

- Backend funcional con FastAPI + SQLAlchemy.
- Frontend funcional con React + TypeScript.
- Integracion de WhatsApp por Twilio activa.
- IA con Groq activa.
- Transcripcion de audio de WhatsApp a texto activa (Groq STT por defecto; local opcional).
- Reglas de negocio de precalificacion activas por defecto.
- Dashboard operativo con WebSocket para actualizacion en tiempo real.

## Que hace hoy

- Recibe mensajes de WhatsApp en `POST /webhook/whatsapp`.
- Si el usuario envia audio, se transcribe a texto y se procesa en el mismo flujo.
- Crea o reutiliza cliente/conversacion.
- Extrae datos con IA (`full_name`, `amount`, `term_months`, `monthly_income`).
- Guia la conversacion por estados:
  - `START`
  - `ASK_NAME`
  - `ASK_AMOUNT`
  - `ASK_TERM`
  - `ASK_INCOME`
  - `SHOW_RESULT`
  - `HANDOFF`
- Evalua reglas de negocio y entrega:
  - `PREAPROBADO`
  - `OBSERVADO`
- En cada respuesta, muestra un resumen de los datos ya registrados del usuario.
- Guarda historial completo en base de datos.
- Permite a un asesor tomar la conversacion y responder desde dashboard.

## Modos de conversacion

Variable: `AI_ONLY_MODE`

- `false` (default): flujo de negocio completo (precalificacion con reglas).
- `true`: modo conversacional IA-only (sin reglas de negocio).

## Reglas de negocio actuales

En `CreditRuleEngine`:

- Si ingreso mensual `< 600` -> `OBSERVADO`.
- Si monto solicitado `> ingreso * 8` -> `OBSERVADO`.
- Si plazo `> 60` meses -> `OBSERVADO`.
- Caso contrario -> `PREAPROBADO`.

## Variables de entorno

Archivo de referencia: `backend/.env.example`

Minimas para pruebas internas:

```env
DATABASE_URL=sqlite:///./credibot.db
GROQ_API_KEY=tu_clave_groq
AI_ONLY_MODE=false
AUDIO_STT_ENABLED=true
AUDIO_STT_PROVIDER=groq
AUDIO_STT_MODEL=base
AUDIO_STT_LANGUAGE=es
AUDIO_STT_DEVICE=cpu
AUDIO_STT_COMPUTE_TYPE=int8
AUDIO_STT_GROQ_MODEL=whisper-large-v3-turbo
AUDIO_STT_REQUEST_TIMEOUT_SECONDS=20
```

`AUDIO_STT_PROVIDER` soporta:

- `groq` (recomendado para webhook en tiempo real).
- `local` (usa faster-whisper local).
- `groq_local_fallback` (intenta Groq y si falla usa local).

Para WhatsApp real (Twilio):

```env
TWILIO_ENABLED=true
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
TWILIO_WHATSAPP_NUMBER=+14155238886
TWILIO_WEBHOOK_URL=https://tu-dominio-o-ngrok/webhook/whatsapp
```

Notas:

- `TWILIO_ACCOUNT_SID` debe empezar con `AC...`.
- No usar API Key `SK...` como `ACCOUNT_SID`.
- Si no quieres PostgreSQL en local, usa `DATABASE_URL` con SQLite.

## Ejecucion local

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Prueba por WhatsApp (Sandbox)

1. Exponer backend con ngrok al puerto `8000`.
2. En Twilio Sandbox, configurar:
   - `When a message comes in`: `https://<ngrok>/webhook/whatsapp`
   - Metodo: `POST`
3. Unir tu numero al sandbox con el `join ...` de Twilio.
4. Enviar mensaje por WhatsApp.

## Endpoints utiles

### Webhook

- `POST /webhook/whatsapp`

### Dashboard API

- `GET /api/dashboard/stats`
- `GET /api/dashboard/conversations`
- `GET /api/dashboard/conversations/{id}/messages`
- `POST /api/dashboard/conversations/{id}/take`
- `POST /api/dashboard/conversations/{id}/reply`

### Salud

- `GET /health`

## Pendientes reales

- Autenticacion y autorizacion del dashboard (JWT/roles).
- Validacion de firma del webhook de Twilio.
- Endurecimiento de seguridad (rate limit, auditoria, manejo de secretos).
- Despliegue productivo (infra, dominio, HTTPS, observabilidad).
- Mejoras UX del panel y analitica avanzada.
