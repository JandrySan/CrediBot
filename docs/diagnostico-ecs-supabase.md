# Diagnostico ECS, OIDC y Supabase

Estado observado el 2026-07-13:

- CI backend y frontend pasan en GitHub Actions.
- GitHub Actions tiene configuradas las variables `AWS_REGION`, `AWS_ECR_REPOSITORY`, `AWS_ECS_CLUSTER`, `AWS_ECS_SERVICE`, `AWS_ECS_CONTAINER_NAME`.
- GitHub Actions tiene configurado el secret `AWS_ROLE_ARN`.
- El CD falla antes de desplegar con:

```text
Could not assume role with OIDC: Not authorized to perform sts:AssumeRoleWithWebIdentity
```

Esto significa que el problema actual del CD esta en AWS IAM/OIDC, no todavia en ECR/ECS.

## 1. Corregir trust policy del rol OIDC

Ejecutar en AWS CloudShell con una identidad que pueda administrar IAM:

```bash
cat > /tmp/credibot-github-actions-trust.json <<'JSON'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::514090178790:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
        },
        "StringLike": {
          "token.actions.githubusercontent.com:sub": "repo:JandrySan/CrediBot:ref:refs/heads/main"
        }
      }
    }
  ]
}
JSON

aws iam update-assume-role-policy \
  --role-name github-actions-credibot-deploy \
  --policy-document file:///tmp/credibot-github-actions-trust.json
```

Verificar que quedo aplicado:

```bash
aws iam get-role \
  --role-name github-actions-credibot-deploy \
  --query 'Role.AssumeRolePolicyDocument' \
  --output json
```

Si el OIDC provider no existe, crearlo una sola vez:

```bash
aws iam create-open-id-connect-provider \
  --url https://token.actions.githubusercontent.com \
  --client-id-list sts.amazonaws.com \
  --thumbprint-list 6938fd4d98bab03faadb97b34396831e3780aea1
```

Si ya existe, AWS devolvera error de duplicado y se puede ignorar.

## 2. Verificar task definition activa del servicio

```bash
SERVICE_JSON=$(aws ecs describe-services \
  --cluster credibot-cluster \
  --services credibot-backend-service \
  --region us-east-1)

TASK_DEF_ARN=$(echo "$SERVICE_JSON" | jq -r '.services[0].taskDefinition')
echo "$TASK_DEF_ARN"

aws ecs describe-task-definition \
  --task-definition "$TASK_DEF_ARN" \
  --region us-east-1 \
  --query 'taskDefinition.containerDefinitions[?name==`backend`].[name,environment,secrets]' \
  --output json
```

La salida debe incluir `DATABASE_URL` o `SUPABASE_DATABASE_URL` en `secrets` o `environment`.

## 3. Verificar valor del secret sin imprimirlo completo

Si se usa Secrets Manager:

```bash
aws secretsmanager get-secret-value \
  --secret-id credibot/database-url \
  --region us-east-1 \
  --query 'SecretString' \
  --output text | sed -E 's#(postgresql[^:]*://[^:]+:).+(@[^/]+/).*#\1***\2***#'
```

Debe verse el host de Supabase, por ejemplo:

```text
...@db.subcovtwgoqbitvzoyzy.supabase.co/...
```

Si se ve `localhost`, el secret esta mal y hay que actualizarlo.

## 4. Probar conexion a Supabase desde CloudShell

CloudShell suele tener `psql`. Si no existe, usar el query editor o instalar cliente PostgreSQL temporalmente.

```bash
DATABASE_URL="$(aws secretsmanager get-secret-value \
  --secret-id credibot/database-url \
  --region us-east-1 \
  --query 'SecretString' \
  --output text)"

psql "$DATABASE_URL" -c "select current_database(), current_user, now();"
```

Si Supabase exige SSL y la URL no lo trae, probar con:

```bash
psql "${DATABASE_URL}?sslmode=require" -c "select now();"
```

Para ECS, guardar la URL final con `sslmode=require` si Supabase lo requiere.

## 5. Revisar eventos y logs recientes de ECS

Eventos del servicio:

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

Logs recientes:

```bash
aws logs describe-log-streams \
  --log-group-name /ecs/credibot-backend \
  --order-by LastEventTime \
  --descending \
  --max-items 1 \
  --region us-east-1 \
  --query 'logStreams[0].logStreamName' \
  --output text

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
  --limit 80 \
  --region us-east-1 \
  --query 'events[*].message' \
  --output text
```

## 6. Forzar nuevo despliegue despues de corregir secrets

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

Luego probar:

```bash
curl -i http://credibot-alb-445521082.us-east-1.elb.amazonaws.com/health
```

## 7. Reintentar CD desde GitHub

Cuando el trust policy permita OIDC, reejecutar el workflow `Despliegue backend AWS` desde GitHub Actions o hacer un nuevo push a `main`.
