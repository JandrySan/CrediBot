# Despliegue AWS y CI/CD

Actualizado: 2026-07-13

Este proyecto no tiene app movil. El despliegue productivo actual cubre:

```text
React dashboard -> S3 + CloudFront
WhatsApp/Twilio -> CloudFront /webhook/* -> ALB -> ECS FastAPI
Dashboard /api/* -> CloudFront -> ALB -> ECS FastAPI
Backend -> Supabase PostgreSQL
Backend -> Groq + Twilio + Secrets Manager
GitHub Actions -> OIDC AWS -> ECR/ECS/S3/CloudFront
```

## Estado actual

Recursos confirmados:

| Recurso | Valor |
| --- | --- |
| Region | `us-east-1` |
| Cuenta AWS | `514090178790` |
| IAM role OIDC | `github-actions-credibot-deploy` |
| ECR | `credibot-backend` |
| ECS cluster | `credibot-cluster` |
| ECS service | `credibot-backend-service` |
| ALB | `credibot-alb-445521082.us-east-1.elb.amazonaws.com` |
| Frontend S3 | `credibot-frontend-514090178790-us-east-1` |
| CloudFront distribution | `E3IWLBA195SDM2` |
| Frontend URL | `https://d30z3dsmpm7ctx.cloudfront.net` |
| Supabase ref | `subcovtwgoqbitvzoyzy` |

Rutas productivas:

- Dashboard: `https://d30z3dsmpm7ctx.cloudfront.net`
- Health backend: `https://d30z3dsmpm7ctx.cloudfront.net/api/health`
- API: `https://d30z3dsmpm7ctx.cloudfront.net/api/*`
- WebSocket: `wss://d30z3dsmpm7ctx.cloudfront.net/ws/dashboard`
- Webhook Twilio: `https://d30z3dsmpm7ctx.cloudfront.net/webhook/whatsapp`
- Audio publico: `https://d30z3dsmpm7ctx.cloudfront.net/webhook/audio/{filename}`

## Workflows

### Backend CI

Archivo:

```text
.github/workflows/ci-backend.yml
```

Ejecuta:

- Instala dependencias Python.
- Compila Python.
- Corre pruebas con SQLite.

### Frontend CI

Archivo:

```text
.github/workflows/ci-frontend.yml
```

Ejecuta:

- `npm ci`
- `npm run lint`
- `npm run build`

### Backend CD

Archivo:

```text
.github/workflows/cd-backend-aws.yml
```

Ejecuta:

1. Valida backend.
2. Asume el rol AWS por OIDC.
3. Hace login en ECR.
4. Crea ECR si no existe.
5. Construye imagen Docker desde `backend/Dockerfile`.
6. Publica tags `latest` y `${github.sha}`.
7. Lee la task definition activa del servicio ECS.
8. Valida los secrets requeridos y sincroniza los del dashboard.
9. Ejecuta `alembic upgrade head` contra la base productiva.
10. Registra una task definition con nombres canonicos de entorno y secrets.
11. Actualiza el servicio ECS y espera estabilidad.
12. Verifica health, login JWT y rechazo de webhooks sin firma.

### Frontend CD

Archivo:

```text
.github/workflows/cd-frontend-aws.yml
```

Ejecuta:

1. Valida frontend.
2. Asume el rol AWS por OIDC.
3. Construye el frontend.
4. Sincroniza `dist/` al bucket S3.
5. Invalida CloudFront.

## Variables de GitHub Actions

Variables/secrets requeridos:

| Nombre | Tipo recomendado | Uso |
| --- | --- | --- |
| `AWS_REGION` | Variable | Region AWS. |
| `AWS_ECR_REPOSITORY` | Variable | Repositorio ECR del backend. |
| `AWS_ROLE_ARN` | Secret | Rol OIDC que asume GitHub Actions. |
| `DASHBOARD_ADMIN_PASSWORD` | Secret | Se sincroniza a Secrets Manager sin exponerlo en ECS. |
| `DASHBOARD_JWT_SECRET` | Secret | Clave de firma JWT, minimo 32 caracteres. |
| `AWS_ECS_CLUSTER` | Variable | Cluster ECS. |
| `AWS_ECS_SERVICE` | Variable | Servicio ECS. |
| `AWS_ECS_CONTAINER_NAME` | Variable | Nombre del contenedor backend. |
| `TWILIO_WHATSAPP_FROM` | Variable | Remitente de WhatsApp; es identificador, no credencial. |
| `AWS_S3_FRONTEND_BUCKET` | Variable | Bucket del frontend. |
| `AWS_CLOUDFRONT_DISTRIBUTION_ID` | Variable | Distribucion CloudFront. |
| `FRONTEND_PUBLIC_URL` | Variable | URL publica del dashboard. |

Twilio, Groq y la base de datos no se duplican en GitHub Secrets; sus valores
permanecen exclusivamente en AWS Secrets Manager.

El rol `github-actions-credibot-deploy` necesita el permiso minimo de
Secrets Manager definido en `docs/iam-github-actions-secrets-policy.json`.
Sus permisos de publicacion en ECR y actualizacion de ECS se definen en
`docs/iam-github-actions-ecr-ecs-policy.json`; incluyen la descarga de la
imagen para ejecutar las migraciones antes de actualizar el servicio.
El rol de ejecucion de la task de ECS necesita la politica de
`docs/iam-ecs-secrets-policy.json`; ECS usa ese permiso al inyectar los
secretos en el contenedor.

## Secrets de aplicacion

Los secretos de aplicacion deben estar en AWS Secrets Manager o SSM y llegar a
ECS como `secrets`, no como variables planas.

Secrets actuales esperados:

| Secret | Variable en contenedor |
| --- | --- |
| `credibot/database-url` | `DATABASE_URL` |
| `credibot/groq-api-key` | `GROQ_API_KEY` |
| `credibot/twilio-account-sid` | `TWILIO_ACCOUNT_SID` |
| `credibot/twilio-auth-token` | `TWILIO_AUTH_TOKEN` |
| `credibot/dashboard-admin-password` | `DASHBOARD_ADMIN_PASSWORD` |
| `credibot/dashboard-jwt-secret` | `DASHBOARD_JWT_SECRET` |

`TWILIO_WEBHOOK_URL` se deriva de `FRONTEND_PUBLIC_URL` durante el despliegue.
No es un secreto. El remitente de WhatsApp tampoco es una credencial y se
mantiene como variable de GitHub Actions.

Variables no secretas recomendadas en ECS:

```env
DEBUG=false
AI_ONLY_MODE=false
PORT=8000
TWILIO_ENABLED=true
BACKEND_CORS_ORIGINS=https://d30z3dsmpm7ctx.cloudfront.net
AUDIO_STT_ENABLED=true
AUDIO_STT_PROVIDER=groq
AUDIO_REPLY_ENABLED=true
DASHBOARD_AUTH_ENABLED=true
TWILIO_VALIDATE_SIGNATURE=true
CONVERSATION_SESSION_TIMEOUT_MINUTES=60
CONVERSATION_CLEANUP_BATCH_SIZE=100
ABANDONED_CONVERSATION_RETENTION_DAYS=7
```

## CloudFront

La distribucion sirve frontend y backend bajo el mismo dominio.

Behaviors:

- `/api/*` -> ALB backend.
- `/ws/*` -> ALB backend.
- `/webhook/*` -> ALB backend.
- `/*` -> S3 frontend.

Ventajas:

- No hay contenido mixto.
- El frontend puede usar rutas relativas.
- Twilio puede usar HTTPS aunque el ALB interno siga como HTTP.
- Los audios generados quedan disponibles por HTTPS para Twilio.

## Supabase

Supabase es la base PostgreSQL productiva.

La URL de conexion debe usar PostgreSQL compatible con SQLAlchemy, por ejemplo:

```text
postgresql+psycopg2://...
```

Si Supabase requiere SSL, incluir:

```text
?sslmode=require
```

La central simulada esta en el schema `credit_bureau`.

Aplicar migraciones:

```powershell
npx supabase db push --linked --yes
```

Validar perfil:

```powershell
npx supabase db query --linked "SELECT national_id, full_name, credit_score, risk_level, total_outstanding_debt, max_days_past_due, preliminary_history_result FROM credit_bureau.find_profile('9990000003');"
```

## Twilio

Webhook actual:

```text
https://d30z3dsmpm7ctx.cloudfront.net/webhook/whatsapp
```

Numero sandbox:

```text
whatsapp:+14155238886
```

Para probar:

1. Unirse al sandbox desde WhatsApp si Twilio lo solicita.
2. Enviar `quiero solicitar un credito`.
3. Usar una cedula ficticia, por ejemplo `9990000003`.
4. Completar monto, plazo e ingreso.
5. Probar audio con `responde en audio`.

## Pruebas rapidas de produccion

Dashboard:

```powershell
Invoke-RestMethod https://d30z3dsmpm7ctx.cloudfront.net/api/dashboard/stats
```

Webhook texto:

```powershell
curl.exe -sS -X POST "https://d30z3dsmpm7ctx.cloudfront.net/webhook/whatsapp" `
  -H "Content-Type: application/x-www-form-urlencoded" `
  --data-urlencode "From=whatsapp:+593999881999" `
  --data-urlencode "Body=hola" `
  --data-urlencode "MessageType=text" `
  --data-urlencode "NumMedia=0"
```

Webhook audio saliente:

```powershell
curl.exe -sS -X POST "https://d30z3dsmpm7ctx.cloudfront.net/webhook/whatsapp" `
  -H "Content-Type: application/x-www-form-urlencoded" `
  --data-urlencode "From=whatsapp:+593999881999" `
  --data-urlencode "Body=responde en audio" `
  --data-urlencode "MessageType=text" `
  --data-urlencode "NumMedia=0"
```

La respuesta debe incluir:

```xml
<Media>https://d30z3dsmpm7ctx.cloudfront.net/webhook/audio/archivo.ogg</Media>
```

## Diagnostico ECS

Ver servicio:

```bash
aws ecs describe-services \
  --cluster credibot-cluster \
  --services credibot-backend-service \
  --region us-east-1
```

Eventos recientes:

```bash
aws ecs describe-services \
  --cluster credibot-cluster \
  --services credibot-backend-service \
  --region us-east-1 \
  --query 'services[0].events[0:10].[createdAt,message]' \
  --output table
```

Logs recientes:

```bash
STREAM_NAME="$(aws logs describe-log-streams \
  --log-group-name /ecs/credibot-backend \
  --order-by LastEventTime \
  --descending \
  --max-items 1 \
  --region us-east-1 \
  --query 'logStreams[0].logStreamName' \
  --output text)"

aws logs get-log-events \
  --log-group-name /ecs/credibot-backend \
  --log-stream-name "$STREAM_NAME" \
  --limit 100 \
  --region us-east-1 \
  --query 'events[*].message' \
  --output text
```

## Dominio propio

Pendiente por decision del proyecto.

Cuando se configure:

1. Crear certificado ACM en `us-east-1` si se usa CloudFront.
2. Agregar alias al distribution de CloudFront.
3. Apuntar DNS al distribution.
4. Actualizar `FRONTEND_PUBLIC_URL`.
5. Actualizar `TWILIO_WEBHOOK_URL`.
6. Actualizar CORS.

## Pendientes de produccion real

- Dominio propio.
- Alarmas CloudWatch.
- Rate limiting distribuido si ECS escala a varias tareas.
- Backups y politica de retencion.
- Separar staging/prod.
- Rotacion periodica de secretos.
