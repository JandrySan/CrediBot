# Diagnostico ECS, CloudFront y Supabase

Actualizado: 2026-07-13

Este documento sirve como runbook cuando algo falla en produccion.

## Estado base esperado

- GitHub Actions usa OIDC correctamente.
- Backend CI pasa.
- Frontend CI pasa.
- Backend CD publica imagen en ECR y actualiza ECS.
- Frontend CD publica en S3 e invalida CloudFront.
- ECS service queda estable.
- Supabase responde consultas del schema `credit_bureau`.
- CloudFront enruta `/api/*`, `/ws/*` y `/webhook/*` al backend.
- Twilio apunta a `https://d30z3dsmpm7ctx.cloudfront.net/webhook/whatsapp`.

## 1. Verificar GitHub Actions

```powershell
gh run list --repo JandrySan/CrediBot --limit 10
```

Ver detalle:

```powershell
gh run view <RUN_ID> --repo JandrySan/CrediBot --verbose
```

Si un job falla, revisar logs:

```powershell
gh run view <RUN_ID> --repo JandrySan/CrediBot --log-failed
```

## 2. Verificar CloudFront/API

Stats del dashboard:

```powershell
Invoke-RestMethod https://d30z3dsmpm7ctx.cloudfront.net/api/dashboard/stats
```

Webhook de prueba:

```powershell
curl.exe -sS -X POST "https://d30z3dsmpm7ctx.cloudfront.net/webhook/whatsapp" `
  -H "Content-Type: application/x-www-form-urlencoded" `
  --data-urlencode "From=whatsapp:+593999880001" `
  --data-urlencode "Body=hola" `
  --data-urlencode "MessageType=text" `
  --data-urlencode "NumMedia=0"
```

Debe responder XML de Twilio (`<Response>...</Response>`).

## 3. Verificar audio saliente

```powershell
curl.exe -sS -X POST "https://d30z3dsmpm7ctx.cloudfront.net/webhook/whatsapp" `
  -H "Content-Type: application/x-www-form-urlencoded" `
  --data-urlencode "From=whatsapp:+593999880002" `
  --data-urlencode "Body=responde en audio" `
  --data-urlencode "MessageType=text" `
  --data-urlencode "NumMedia=0"
```

Debe devolver:

```xml
<Media>https://d30z3dsmpm7ctx.cloudfront.net/webhook/audio/....ogg</Media>
```

Validar descarga del audio:

```powershell
curl.exe -sS -L -r 0-63 -o NUL -w "%{http_code} %{content_type} %{size_download}\n" "https://d30z3dsmpm7ctx.cloudfront.net/webhook/audio/<archivo>.ogg"
```

Resultado esperado:

```text
206 audio/ogg 64
```

## 4. Verificar flujo por cedula

Enviar mensajes secuenciales con un numero de prueba nuevo:

```powershell
$url='https://d30z3dsmpm7ctx.cloudfront.net/webhook/whatsapp'
$from='whatsapp:+593999880003'
$messages=@('quiero solicitar un credito','9990000003','1200','12 meses','900')

foreach ($message in $messages) {
  curl.exe -sS -X POST $url `
    -H "Content-Type: application/x-www-form-urlencoded" `
    --data-urlencode "From=$from" `
    --data-urlencode "Body=$message" `
    --data-urlencode "MessageType=text" `
    --data-urlencode "NumMedia=0"
}
```

Resultado esperado:

- Primero pide cedula.
- Con `9990000003` autocompleta `Maria Torres Cedeno`.
- Pide monto, plazo e ingreso.
- Termina con resultado `OBSERVADO`.

Cedulas faciles para pruebas rapidas:

| Cedula | Caso |
| --- | --- |
| `1111111111` | Diego Calva Ortiz, APTO |
| `2222222222` | Jandry San Mendoza, APTO |
| `3333333333` | Joel Andrade Briones, OBSERVADO |
| `4444444444` | Carlos Duty Zambrano, OBSERVADO |
| `5555555555` | Maria Jose Cedeno Lopez, APTO |
| `6666666666` | Andrea Solorzano Vera, APTO |
| `7777777777` | Hugo Valencia Rivas, APTO |
| `8888888888` | Karina Delgado Moreira, APTO por historial |

## 5. Verificar Supabase

Perfil individual:

```powershell
npx supabase db query --linked "SELECT national_id, full_name, central_risk_status, credit_score, risk_level, total_outstanding_debt, max_days_past_due, missed_payments, preliminary_history_result FROM credit_bureau.find_profile('9990000003');"
```

Resultado esperado:

```text
national_id: 9990000003
full_name: Maria Torres Cedeno
credit_score: 485
risk_level: HIGH
total_outstanding_debt: 2100
max_days_past_due: 90
missed_payments: 3
preliminary_history_result: OBSERVADO
```

Vista general:

```powershell
npx supabase db query --linked "SELECT national_id, full_name, credit_score, risk_level, preliminary_history_result FROM credit_bureau.credit_profile_summary ORDER BY national_id LIMIT 20;"
```

## 6. Verificar ECS

Task definition activa:

```bash
SERVICE_JSON=$(aws ecs describe-services \
  --cluster credibot-cluster \
  --services credibot-backend-service \
  --region us-east-1)

TASK_DEF_ARN=$(echo "$SERVICE_JSON" | jq -r '.services[0].taskDefinition')
echo "$TASK_DEF_ARN"
```

Variables y secrets del contenedor:

```bash
aws ecs describe-task-definition \
  --task-definition "$TASK_DEF_ARN" \
  --region us-east-1 \
  --query 'taskDefinition.containerDefinitions[0].[name,environment,secrets]' \
  --output json
```

Debe incluir:

- `DATABASE_URL` o `SUPABASE_DATABASE_URL`.
- `GROQ_API_KEY`.
- `TWILIO_*`.
- `AUDIO_REPLY_ENABLED=true`.
- `AUDIO_REPLY_PUBLIC_BASE_URL=https://d30z3dsmpm7ctx.cloudfront.net`.

## 7. Ver eventos y logs ECS

Eventos:

```bash
aws ecs describe-services \
  --cluster credibot-cluster \
  --services credibot-backend-service \
  --region us-east-1 \
  --query 'services[0].events[0:10].[createdAt,message]' \
  --output table
```

Tareas detenidas:

```bash
aws ecs list-tasks \
  --cluster credibot-cluster \
  --service-name credibot-backend-service \
  --desired-status STOPPED \
  --region us-east-1 \
  --query 'taskArns[0:5]' \
  --output text
```

Detalle de la ultima tarea detenida:

```bash
TASK_ARN=$(aws ecs list-tasks \
  --cluster credibot-cluster \
  --service-name credibot-backend-service \
  --desired-status STOPPED \
  --region us-east-1 \
  --query 'taskArns[0]' \
  --output text)

aws ecs describe-tasks \
  --cluster credibot-cluster \
  --tasks "$TASK_ARN" \
  --region us-east-1 \
  --query 'tasks[0].containers[0].[lastStatus,exitCode,reason]' \
  --output table
```

Logs:

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

## 8. Problemas comunes

### ECS arranca pero falla con localhost PostgreSQL

Causa: `DATABASE_URL` no esta llegando o apunta a `localhost`.

Validar secret sin imprimirlo completo:

```bash
aws secretsmanager get-secret-value \
  --secret-id credibot/database-url \
  --region us-east-1 \
  --query 'SecretString' \
  --output text | sed -E 's#(postgresql[^:]*://[^:]+:).+(@[^/]+/).*#\1***\2***#'
```

### Audio vuelve como texto

Validar:

- `AUDIO_REPLY_ENABLED=true`
- `AUDIO_REPLY_PUBLIC_BASE_URL=https://d30z3dsmpm7ctx.cloudfront.net`
- CloudFront enruta `/webhook/*`.
- El endpoint `GET /webhook/audio/{filename}` responde `audio/ogg`.

### Resultado OBSERVADO rompe al guardar

Ya se corrigio convirtiendo `credit_applications.reason` a `TEXT`.

Si vuelve a pasar, validar que la task nueva haya arrancado y que `init_db()` se
ejecuto contra PostgreSQL.

### OIDC falla en GitHub Actions

Error tipico:

```text
Could not assume role with OIDC
```

Validar trust policy del rol `github-actions-credibot-deploy`:

```json
{
  "StringEquals": {
    "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
  },
  "StringLike": {
    "token.actions.githubusercontent.com:sub": "repo:JandrySan/CrediBot:ref:refs/heads/main"
  }
}
```

## 9. Forzar nuevo despliegue ECS

```bash
aws ecs update-service \
  --cluster credibot-cluster \
  --service credibot-backend-service \
  --force-new-deployment \
  --region us-east-1

aws ecs wait services-stable \
  --cluster credibot-cluster \
  --services credibot-backend-service \
  --region us-east-1
```

## 10. Reejecutar despliegue desde GitHub

```powershell
gh workflow run "Despliegue backend AWS" --repo JandrySan/CrediBot --ref main
```

Ver progreso:

```powershell
gh run list --repo JandrySan/CrediBot --limit 5
```
