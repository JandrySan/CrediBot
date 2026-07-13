# CrediBot

MVP de asistente de precalificacion de creditos por WhatsApp.

Actualizado: 2026-07-13

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
- Si `AUDIO_REPLY_ENABLED=true`, el bot genera un `.ogg` y responde con
  `<Media>`.
- Si falla la generacion o descarga del audio, cae a texto.
- El usuario puede volver con `responde en texto`.

Frases reconocidas:

- Audio: `responde en audio`, `modo audio`, `quiero voz`, `nota de voz`.
- Texto: `responde en texto`, `modo texto`, `solo texto`, `por escrito`.

En produccion, el workflow de backend fuerza:

```env
AUDIO_REPLY_ENABLED=true
AUDIO_REPLY_LANGUAGE=es
AUDIO_REPLY_PUBLIC_BASE_URL=https://d30z3dsmpm7ctx.cloudfront.net
```

## Dashboard

El dashboard permite:

- Ver estadisticas generales.
- Listar conversaciones.
- Ver mensajes de una conversacion.
- Ver cedula, nombre y datos de solicitud.
- Tomar una conversacion como asesor.
- Responder al cliente por WhatsApp.
- Cerrar una conversacion en `HANDOFF`.
- Administrar FAQs.
- Disparar limpieza de conversaciones expiradas.

Rutas frontend:

- `/`: panel principal.
- `/faqs`: administracion de FAQs.

## Endpoints

App:

- `GET /`
- `GET /health`

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
SUPABASE_DATABASE_URL=
GROQ_API_KEY=
AI_ONLY_MODE=false

TWILIO_ENABLED=true
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
TWILIO_WHATSAPP_NUMBER=+14155238886
TWILIO_WEBHOOK_URL=https://d30z3dsmpm7ctx.cloudfront.net/webhook/whatsapp

AUDIO_STT_ENABLED=true
AUDIO_STT_PROVIDER=groq
AUDIO_STT_GROQ_MODEL=whisper-large-v3-turbo
AUDIO_REPLY_ENABLED=true
AUDIO_REPLY_LANGUAGE=es
AUDIO_REPLY_PUBLIC_BASE_URL=https://d30z3dsmpm7ctx.cloudfront.net

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
- `credibot/twilio-whatsapp-number`

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
VITE_WS_BASE_URL=ws://127.0.0.1:8000
```

En produccion, si `VITE_API_BASE_URL` no se define, el frontend usa el mismo
origen del navegador. Esto permite que `/api/*`, `/ws/*` y `/webhook/*` salgan
por CloudFront.

## Ejecucion local

Backend:

```powershell
cd backend
python -m pip install -r requirements.txt
$env:DATABASE_URL="sqlite:///./credibot_dev.db"
$env:DEBUG="false"
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

Frontend:

```powershell
cd frontend
npm install
npm run dev
```

Pruebas backend:

```powershell
cd backend
$env:DATABASE_URL="sqlite:///./credibot_test.db"
$env:DEBUG="false"
python -m pytest
```

Validacion frontend:

```powershell
cd frontend
npm run lint
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

Estado validado el 2026-07-13:

- Supabase actualizado con central simulada enriquecida.
- `credit_bureau.find_profile('9990000003')` devuelve Maria Torres Cedeno,
  score 485, riesgo HIGH, deuda 2100, mora maxima 90 y resultado `OBSERVADO`.
- Backend local: 49 pruebas pasando.
- Frontend: lint y build correctos.
- GitHub Actions: backend/frontend validan y despliegan.
- CloudFront responde dashboard y API.
- Webhook WhatsApp responde por texto.
- Preferencia `responde en audio` devuelve `<Media>` con archivo `audio/ogg`.
- Flujo completo con cedula `9990000003` termina en `OBSERVADO`.

## Pendientes recomendados

- Configurar dominio propio y certificado ACM.
- Mover cualquier variable sensible restante a Secrets Manager/SSM.
- Rotar secretos que hayan sido compartidos fuera de gestores seguros.
- Validar firma de webhooks Twilio.
- Agregar autenticacion y roles al dashboard.
- Agregar rate limiting.
- Mejorar observabilidad con alarmas CloudWatch.
- Separar ambientes staging/prod.
- Deduplicar conversaciones por cliente si se necesita una vista mas ejecutiva.
- Cambiar el guardado de mensajes del asesor para marcar envio exitoso/fallido.
