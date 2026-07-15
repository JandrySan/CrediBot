# CrediBot

MVP de asistente de precalificacion de creditos por WhatsApp.

Actualizado: 2026-07-15

## Estado actual

CrediBot esta desplegado en AWS y usa Supabase como PostgreSQL productivo. El
frontend se sirve desde S3 + CloudFront y el backend corre en ECS Fargate. El
flujo principal de WhatsApp esta conectado por Twilio Sandbox.

URLs actuales:

- Frontend/dashboard: `https://d30z3dsmpm7ctx.cloudfront.net`
- API por CloudFront: `https://d30z3dsmpm7ctx.cloudfront.net/api/...`
- Webhook WhatsApp: `https://d30z3dsmpm7ctx.cloudfront.net/webhook/whatsapp`
- Audios generados: `https://d30z3dsmpm7ctx.cloudfront.net/webhook/audio/{filename}`

Numero de prueba Twilio Sandbox:

```text
+1 415 523 8886
```

En Twilio/WhatsApp se usa como:

```text
whatsapp:+14155238886
```

## Que hace

CrediBot automatiza la primera atencion de solicitudes de credito por WhatsApp.
El usuario puede escribir texto o enviar audio. El sistema transcribe audios,
extrae datos con IA, consulta una central de riesgo simulada en Supabase, aplica
reglas de negocio auditables y guarda el resultado para que un asesor lo revise
desde el dashboard.

Componentes:

- Backend: FastAPI + SQLAlchemy.
- Base de datos: PostgreSQL en Supabase.
- Frontend: React + TypeScript + Vite + MUI.
- WhatsApp: Twilio Sandbox.
- IA: Groq.
- Audio entrante: transcripcion con Groq STT.
- Audio saliente: gTTS + OGG/Opus con PyAV.
- Frontend productivo: S3 + CloudFront.
- Backend productivo: ECR + ECS Fargate + ALB.
- CI/CD: GitHub Actions con OIDC hacia AWS.

## Flujo principal

```text
Usuario WhatsApp
  -> Twilio Sandbox
  -> CloudFront /webhook/*
  -> ALB
  -> ECS FastAPI
  -> Supabase PostgreSQL
  -> Groq / reglas / central simulada
  -> Twilio
  -> Usuario WhatsApp
```

## Flujo de precalificacion

1. El usuario escribe por WhatsApp.
2. Twilio llama `POST /webhook/whatsapp`.
3. Si el mensaje trae audio, se transcribe y entra al mismo flujo de texto.
4. El bot saluda y pregunta la cedula cuando el usuario quiere precalificar.
5. La cedula se busca en la central de riesgo simulada.
6. Si la cedula existe, se autocompleta el nombre.
7. Si no existe, el bot pide nombre completo.
8. El bot pide monto, plazo e ingreso mensual.
9. El motor de reglas calcula una decision preliminar.
10. La central simulada puede convertir el resultado en `OBSERVADO`.
11. Se guarda la conversacion, solicitud, mensajes, analisis IA y cambios de estado.
12. El dashboard recibe eventos por WebSocket.

Cedulas ficticias utiles para pruebas:

| Cedula | Perfil | Resultado esperado |
| --- | --- | --- |
| `1111111111` | Diego Calva Ortiz, score 805, riesgo bajo | `APTO` |
| `2222222222` | Jandry San Mendoza, score 682, riesgo medio | `APTO` |
| `3333333333` | Joel Andrade Briones, score 540, mora y pagos incumplidos | `OBSERVADO` |
| `4444444444` | Carlos Duty Zambrano, score 405, cobranza judicial | `OBSERVADO` |
| `5555555555` | Maria Jose Cedeno Lopez, score 735, riesgo bajo | `APTO` |
| `6666666666` | Andrea Solorzano Vera, estudiante, riesgo medio | `APTO` |
| `7777777777` | Hugo Valencia Rivas, jubilado, riesgo bajo | `APTO` |
| `8888888888` | Karina Delgado Moreira, autonoma con deuda alta | `APTO` por historial, revisar capacidad por reglas |
| `9990000003` | Maria Torres Cedeno, score 485, mora maxima 90 dias | `OBSERVADO` |
| `9990000014` | Roberto Quiroz Velez, score 420, cobranza judicial | `OBSERVADO` |
| `9990000012` | Hugo Andrade Cevallos, score 790, riesgo bajo | perfil favorable |

## Central de riesgo simulada

La central de riesgo vive en el schema `credit_bureau` de Supabase.

Migraciones relevantes:

- `supabase/migrations/20260713005730_credit_bureau_simulation.sql`
- `supabase/migrations/20260713070000_enrich_credit_bureau_simulation.sql`

Tablas y objetos principales:

- `credit_bureau.people`
- `credit_bureau.credit_accounts`
- `credit_bureau.payment_history`
- `credit_bureau.credit_score_snapshots`
- `credit_bureau.risk_events`
- `credit_bureau.credit_inquiries`
- `credit_bureau.credit_profile_summary`
- `credit_bureau.find_profile(identifier TEXT)`

Consulta rapida:

```sql
SELECT *
FROM credit_bureau.find_profile('9990000003');
```

Campos usados por el bot:

- `national_id`
- `full_name`
- `employment_status`
- `reported_monthly_income`
- `central_risk_status`
- `central_risk_reason`
- `credit_score`
- `risk_level`
- `total_outstanding_debt`
- `total_monthly_debt_payment`
- `debt_to_income_ratio`
- `max_days_past_due`
- `missed_payments`
- `late_payments`
- `written_off_accounts`
- `judicial_collection_events`
- `restructured_accounts`
- `recent_inquiries_6m`
- `recommended_max_installment`
- `preliminary_history_result`

## Estados de conversacion

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

El primer dato requerido para una precalificacion normal es `national_id`.

## Reglas de negocio

Archivo: `backend/app/services/rules/credit_rule_engine.py`

Reglas base:

- Si `monthly_income < 600` -> `OBSERVADO`.
- Si `amount > monthly_income * 8` -> `OBSERVADO`.
- Si `term_months > 60` -> `OBSERVADO`.
- Caso contrario -> `PREAPROBADO`.

Luego se consulta la central simulada. Si `preliminary_history_result` es
`OBSERVADO`, el resultado final queda `OBSERVADO` aunque las reglas base pasen.

La IA no aprueba creditos. La IA ayuda a detectar intencion, extraer datos,
pulir respuestas y responder FAQs; la decision sale de reglas explicitas y de la
central simulada.

## Audio

CrediBot soporta audio en dos direcciones.

Entrada:

- El usuario envia una nota de voz a WhatsApp.
- Twilio entrega el archivo al webhook.
- `SpeechToTextService` descarga y transcribe.
- El texto transcrito entra al flujo normal.

Salida:

- El usuario puede escribir `responde en audio`.
- La preferencia queda guardada en `conversations.response_mode`.
- El comando puro de cambio de modo se confirma en texto para evitar una nota
  de voz confusa al inicio.
- Si `AUDIO_REPLY_ENABLED=true`, el bot genera un `.ogg` y responde con
  `<Media>` desde el siguiente mensaje de negocio.
- Si falla la generacion o descarga del audio, cae a texto.
- El usuario puede volver con `responde en texto`.

Frases reconocidas:

- Audio: `responde en audio`, `modo audio`, `quiero voz`, `nota de voz`.
- Texto: `responde en texto`, `modo texto`, `solo texto`, `por escrito`.

En produccion, el workflow de backend fuerza:

```env
AUDIO_REPLY_ENABLED=true
```

El idioma es espanol y la URL de audio se deriva de `TWILIO_WEBHOOK_URL`.

## Dashboard

El dashboard permite:

- Ver estadisticas generales.
- Listar conversaciones.
- Ver mensajes de una conversacion.
- Ver cedula, nombre y datos de solicitud.
- Tomar una conversacion como asesor.
- Responder al cliente por WhatsApp.
- Al tomar una conversacion, el backend fuerza `response_mode=TEXT` y avisa al
  cliente que un asesor humano tomo el caso.
- Las respuestas manuales del asesor solo se guardan como enviadas si Twilio
  confirma el envio.
- Cerrar una conversacion en `HANDOFF`.
- Administrar FAQs.
- Disparar limpieza de conversaciones expiradas.

Rutas frontend:

- `/panel`: resumen operativo.
- `/conversaciones`: bandeja de conversaciones y atencion del asesor.
- `/faqs`: administracion de FAQs.
- `/analitica`: metricas operativas y de precalificacion.
- `/configuracion`: estado de API, WebSocket y webhook.

## Endpoints

App:

- `GET /`
- `GET /health`

Autenticacion:

- `GET /api/auth/config`
- `POST /api/auth/token`

WhatsApp:

- `POST /webhook/whatsapp`
- `GET /webhook/audio/{filename}`

Dashboard:

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

WebSocket:

- `GET /ws/dashboard`

El dashboard usa JWT con roles `admin` y `advisor`. El WebSocket recibe el
token en el parametro `token`. En desarrollo local se puede desactivar con
`DASHBOARD_AUTH_ENABLED=false`; no debe desactivarse en produccion.

## Variables de entorno backend

Archivo local:

```text
backend/.env
```

Referencia:

```text
backend/.env.example
```

Variables principales:

```env
DATABASE_URL=
RUN_DB_MIGRATIONS=true
AUTO_CREATE_DB_SCHEMA=false
GROQ_API_KEY=
AI_ONLY_MODE=false

TWILIO_ENABLED=true
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
TWILIO_WEBHOOK_URL=https://d30z3dsmpm7ctx.cloudfront.net/webhook/whatsapp
TWILIO_VALIDATE_SIGNATURE=true

DASHBOARD_AUTH_ENABLED=true
DASHBOARD_ADMIN_USERNAME=admin
DASHBOARD_ADMIN_PASSWORD=
DASHBOARD_ADVISOR_USERNAME=
DASHBOARD_ADVISOR_PASSWORD=
DASHBOARD_JWT_SECRET=

AUDIO_STT_ENABLED=true
AUDIO_STT_PROVIDER=groq
AUDIO_STT_GROQ_MODEL=whisper-large-v3-turbo
AUDIO_REPLY_ENABLED=true

BACKEND_CORS_ORIGINS=https://d30z3dsmpm7ctx.cloudfront.net
CONVERSATION_SESSION_TIMEOUT_MINUTES=60
CONVERSATION_CLEANUP_BATCH_SIZE=100
ABANDONED_CONVERSATION_RETENTION_DAYS=7
```

En AWS, los valores sensibles deben vivir en Secrets Manager o SSM, no en el
repositorio.

Secrets usados en produccion:

- `credibot/database-url`
- `credibot/groq-api-key`
- `credibot/twilio-account-sid`
- `credibot/twilio-auth-token`
- `credibot/twilio-webhook-url`
- `credibot/twilio-whatsapp-from`
- `credibot/dashboard-admin-password`
- `credibot/dashboard-jwt-secret`

GitHub solo conserva tres secrets: `AWS_ROLE_ARN`,
`DASHBOARD_ADMIN_PASSWORD` y `DASHBOARD_JWT_SECRET`. Las credenciales de
base de datos, Groq y Twilio viven exclusivamente en AWS Secrets Manager.

Variables eliminadas por redundancia: `SUPABASE_DATABASE_URL`, `DB_HOST`,
`DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `TWILIO_WHATSAPP_NUMBER`,
`AUDIO_STT_LANGUAGE`, `AUDIO_REPLY_LANGUAGE`,
`AUDIO_REPLY_PUBLIC_BASE_URL`, `APP_NAME` y `VITE_WS_BASE_URL`.

## Variables frontend

Archivo local:

```text
frontend/.env
```

Referencia:

```text
frontend/.env.example
```

Variables:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

El WebSocket se deriva automaticamente de la URL de API.

En produccion, si `VITE_API_BASE_URL` no se define, el frontend usa el mismo
origen del navegador. Esto permite que `/api/*`, `/ws/*` y `/webhook/*` salgan
por CloudFront.

## Instalacion, ejecucion y uso

### Requisitos previos

- Python 3.12 o compatible.
- Node.js 20 o compatible.
- PostgreSQL local, Supabase o SQLite para pruebas rapidas.
- Cuenta Twilio con WhatsApp Sandbox si se quiere probar WhatsApp.
- Cuenta Groq si se usara IA, STT o respuestas conversacionales.
- ngrok o dominio publico si Twilio debe llegar a un backend local.

### Instalacion backend

Desde la raiz del proyecto:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\activate
python -m pip install -r requirements-dev.txt
```

Crear o actualizar `backend/.env` usando `backend/.env.example` como base.

El inicio del backend ejecuta `alembic upgrade head` cuando
`RUN_DB_MIGRATIONS=true`. Para aplicar o inspeccionar migraciones manualmente:

```powershell
python -m alembic upgrade head
python -m alembic current
```

Para desarrollo rapido con SQLite:

```powershell
$env:DATABASE_URL="sqlite:///./credibot_dev.db"
$env:DEBUG="false"
```

Para usar Supabase/PostgreSQL:

```env
DATABASE_URL=postgresql+psycopg2://USER:PASSWORD@HOST:PORT/DB
```

Variables minimas recomendadas para probar el bot:

```env
GROQ_API_KEY=
AI_ONLY_MODE=false
TWILIO_ENABLED=true
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
TWILIO_WEBHOOK_URL=https://TU_BACKEND_PUBLICO/webhook/whatsapp
TWILIO_VALIDATE_SIGNATURE=true
AUDIO_REPLY_ENABLED=true
DASHBOARD_AUTH_ENABLED=false
CONVERSATION_SESSION_TIMEOUT_MINUTES=60
ABANDONED_CONVERSATION_RETENTION_DAYS=7
```

Ejecutar backend:

```powershell
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

En desarrollo, tambien se puede usar recarga automatica:

```powershell
python -m uvicorn main:app --reload
```

### Instalacion frontend

```powershell
cd frontend
npm install
```

Crear `frontend/.env` si se quiere apuntar a un backend especifico:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

Ejecutar frontend:

```powershell
npm run dev
```

Abrir:

```text
http://localhost:5173
```

### Prueba local con Twilio

1. Levantar backend en el puerto `8000`.
2. Exponer el backend con ngrok:

```powershell
ngrok http 8000
```

3. Configurar en Twilio Sandbox:

```text
When a message comes in: https://TU_NGROK/webhook/whatsapp
Method: POST
```

4. Actualizar `backend/.env`:

```env
TWILIO_WEBHOOK_URL=https://TU_NGROK/webhook/whatsapp
```

5. Reiniciar backend.
6. Unir el telefono al sandbox con el codigo `join ...`.
7. Enviar mensajes al numero de Twilio Sandbox.

### Uso del sistema

WhatsApp:

- Escribir `hola` muestra una bienvenida abierta.
- Escribir `quiero un credito` inicia la precalificacion.
- El bot solicita cedula, nombre si aplica, monto, plazo e ingreso mensual.
- Con cedulas de prueba consulta la central de riesgo simulada.
- El resultado final puede ser `PREAPROBADO` u `OBSERVADO`.
- Escribir `asesor` deriva la conversacion al dashboard.
- Escribir `responde en audio` activa respuestas por audio.
- Escribir `responde en texto` vuelve a texto.

Dashboard:

- `/panel`: ver resumen operativo.
- `/conversaciones`: atender chats, tomar casos, responder y cerrar conversaciones.
- `/faqs`: cargar, listar y eliminar FAQs.
- `/analitica`: revisar indicadores.
- `/configuracion`: revisar URLs de API, WebSocket y webhook.

Conversaciones:

- Una sesion se cierra por inactividad tras `CONVERSATION_SESSION_TIMEOUT_MINUTES`.
- Las conversaciones abandonadas se purgan tras `ABANDONED_CONVERSATION_RETENTION_DAYS`.
- Las conversaciones cerradas vacias no se muestran en el dashboard.

### Validacion y pruebas

Pruebas backend:

```powershell
cd backend
.\.venv\Scripts\activate
python -m ruff format --check .
python -m ruff check .
python -m mypy app
python -m pytest --cov=app --cov-report=term --cov-report=xml
```

Validacion frontend:

```powershell
cd frontend
npm run lint
npm test
npm run build
```

## CI/CD

Workflows:

- `.github/workflows/ci-backend.yml`
- `.github/workflows/ci-frontend.yml`
- `.github/workflows/cd-backend-aws.yml`
- `.github/workflows/cd-frontend-aws.yml`

El backend se despliega a ECR/ECS. El frontend se despliega a S3/CloudFront.

Documentacion operativa:

- `docs/despliegue-aws.md`
- `docs/diagnostico-ecs-supabase.md`

## Verificacion realizada

Estado validado el 2026-07-15:

- Supabase actualizado con central simulada enriquecida.
- `credit_bureau.find_profile('9990000003')` devuelve Maria Torres Cedeno,
  score 485, riesgo HIGH, deuda 2100, mora maxima 90 y resultado `OBSERVADO`.
- Backend local: 58 pruebas pasando y cobertura superior al 60%.
- Backend: Ruff, formato y Mypy correctos.
- Frontend: lint, pruebas y build correctos.
- Migraciones Alembic validadas en SQLite vacio y PostgreSQL local existente.
- Dashboard protegido con JWT y roles; webhook Twilio con validacion de firma.
- GitHub Actions: backend/frontend validan y despliegan.
- CloudFront responde dashboard y API.
- Webhook WhatsApp responde por texto.
- Preferencia `responde en audio` devuelve `<Media>` con archivo `audio/ogg`.
- Flujo completo con cedula `9990000003` termina en `OBSERVADO`.

## Pendientes recomendados

- Configurar dominio propio y certificado ACM.
- Mover cualquier variable sensible restante a Secrets Manager/SSM.
- Rotar secretos que hayan sido compartidos fuera de gestores seguros.
- Mejorar observabilidad con alarmas CloudWatch.
- Separar ambientes staging/prod.
- Deduplicar conversaciones por cliente si se necesita una vista mas ejecutiva.
- Sustituir el rate limiter en memoria por Redis si se ejecutan varias tareas ECS.
