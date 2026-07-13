# Despliegue AWS y CI/CD

Este proyecto no tiene app movil. El flujo productivo cubierto aqui es:

```text
Dashboard web React -> Backend FastAPI -> PostgreSQL/Supabase o RDS
WhatsApp/Twilio -> Backend FastAPI -> Groq/Twilio/PostgreSQL
GitHub Actions -> OIDC AWS -> ECR -> ECS Fargate
```

## Que se implemento

- `backend/Dockerfile` para ejecutar FastAPI en contenedor.
- Healthcheck Docker contra `GET /health`.
- CI de backend en GitHub Actions con instalacion, verificacion de sintaxis y pruebas.
- CI de frontend con `npm ci`, lint y build.
- CD de backend a AWS con OIDC, publicacion en ECR y actualizacion de ECS.
- URL de API y WebSocket configurables en el frontend con variables Vite.
- CORS configurable en el backend con `BACKEND_CORS_ORIGINS`.

## Variables de GitHub Actions

Crear estas variables o secrets en GitHub:

| Nombre | Tipo recomendado | Uso |
| --- | --- | --- |
| `AWS_REGION` | Variable | Region AWS, por ejemplo `us-east-1`. |
| `AWS_ECR_REPOSITORY` | Variable | Nombre del repositorio ECR, por ejemplo `credibot-backend`. |
| `AWS_ROLE_ARN` | Secret | ARN del rol IAM que GitHub Actions asume por OIDC. |
| `AWS_ECS_CLUSTER` | Variable | Nombre del cluster ECS. |
| `AWS_ECS_SERVICE` | Variable | Nombre del servicio ECS del backend. |
| `AWS_ECS_CONTAINER_NAME` | Variable opcional | Nombre del contenedor si la task definition tiene mas de un contenedor. |

Secrets de aplicacion que deben llegar al backend desde ECS, no desde el codigo:

| Nombre | Uso |
| --- | --- |
| `DATABASE_URL` o `SUPABASE_DATABASE_URL` | Conexion PostgreSQL productiva. |
| `GROQ_API_KEY` | IA y STT con Groq. |
| `TWILIO_ACCOUNT_SID` | Cuenta Twilio. |
| `TWILIO_AUTH_TOKEN` | Token Twilio. |
| `TWILIO_WHATSAPP_FROM` | Numero WhatsApp emisor, por ejemplo `whatsapp:+14155238886`. |
| `TWILIO_WHATSAPP_NUMBER` | Numero base de Twilio si el proyecto lo requiere. |
| `TWILIO_WEBHOOK_URL` | URL publica del webhook, por ejemplo `https://api.midominio.com/webhook/whatsapp`. |
| `AUDIO_REPLY_PUBLIC_BASE_URL` | URL publica base si se habilitan notas de voz. |

## Rol IAM para GitHub Actions

Usar OIDC de GitHub, no access keys estaticas. El trust relationship debe limitar el acceso al repositorio:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::<ACCOUNT_ID>:oidc-provider/token.actions.githubusercontent.com"
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
```

Permisos minimos del rol:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ecr:GetAuthorizationToken"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "ecr:BatchCheckLayerAvailability",
        "ecr:BatchGetImage",
        "ecr:CompleteLayerUpload",
        "ecr:CreateRepository",
        "ecr:DescribeRepositories",
        "ecr:InitiateLayerUpload",
        "ecr:PutImage",
        "ecr:UploadLayerPart"
      ],
      "Resource": "arn:aws:ecr:<AWS_REGION>:<ACCOUNT_ID>:repository/<AWS_ECR_REPOSITORY>"
    },
    {
      "Effect": "Allow",
      "Action": [
        "ecs:DescribeClusters",
        "ecs:DescribeServices",
        "ecs:DescribeTaskDefinition",
        "ecs:RegisterTaskDefinition",
        "ecs:UpdateService"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "iam:PassRole"
      ],
      "Resource": [
        "arn:aws:iam::<ACCOUNT_ID>:role/<ECS_TASK_ROLE>",
        "arn:aws:iam::<ACCOUNT_ID>:role/<ECS_TASK_EXECUTION_ROLE>"
      ]
    }
  ]
}
```

## Recursos AWS esperados

La opcion recomendada para este backend es ECS Fargate con Application Load Balancer:

- ECR: repositorio de imagenes del backend.
- ECS cluster: `desiredCount = 1` para demo.
- ECS task definition: contenedor escuchando `PORT=8000`.
- ECS service: asociado al target group del ALB.
- Application Load Balancer publico.
- Target group HTTP apuntando al puerto `8000` y health check `/health`.
- CloudWatch Logs para la salida del contenedor.
- Secrets Manager o SSM Parameter Store para secretos de aplicacion.
- PostgreSQL productivo: Supabase si el equipo ya lo usa, o RDS PostgreSQL.

No se deben usar bases dentro del contenedor ni SQLite para produccion porque los datos se perderian.

## HTTPS

Para produccion se recomienda:

1. Crear certificado en ACM para el dominio final.
2. Crear listener HTTPS `443` en el ALB.
3. Redirigir HTTP `80` a HTTPS.
4. Configurar `BACKEND_CORS_ORIGINS` con el dominio del dashboard web.
5. Configurar Twilio con `https://<dominio>/webhook/whatsapp`.

Sin dominio propio, el ALB entrega HTTP. Para HTTPS sin dominio de aplicacion se puede poner CloudFront delante, pero lo mas limpio a largo plazo es ACM + ALB + dominio.

## Variables del backend en ECS

Variables no secretas recomendadas:

```env
APP_NAME=CrediBot
DEBUG=false
AI_ONLY_MODE=false
PORT=8000
BACKEND_CORS_ORIGINS=https://dashboard.midominio.com
TWILIO_ENABLED=true
AUDIO_STT_ENABLED=true
AUDIO_STT_PROVIDER=groq
AUDIO_REPLY_ENABLED=false
CONVERSATION_SESSION_TIMEOUT_MINUTES=60
CONVERSATION_CLEANUP_BATCH_SIZE=100
```

Variables secretas desde Secrets Manager o SSM:

```env
DATABASE_URL=postgresql+psycopg2://...
# Alternativa aceptada por la app:
SUPABASE_DATABASE_URL=postgresql+psycopg2://...
GROQ_API_KEY=...
TWILIO_ACCOUNT_SID=...
TWILIO_AUTH_TOKEN=...
TWILIO_WHATSAPP_FROM=...
TWILIO_WHATSAPP_NUMBER=...
TWILIO_WEBHOOK_URL=https://api.midominio.com/webhook/whatsapp
```

## Configuracion del frontend web

Crear `frontend/.env` local desde `frontend/.env.example`:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
VITE_WS_BASE_URL=ws://127.0.0.1:8000
```

Para un build productivo:

```env
VITE_API_BASE_URL=https://api.midominio.com
VITE_WS_BASE_URL=wss://api.midominio.com
```

Si `VITE_WS_BASE_URL` no se configura, el frontend lo deriva desde `VITE_API_BASE_URL`.

## Como se despliega

1. Hacer merge a `main`.
2. GitHub Actions ejecuta `Validacion backend`.
3. Si pasa, el workflow `Despliegue backend AWS`:
   - valida variables requeridas;
   - asume el rol AWS por OIDC;
   - crea el repositorio ECR si no existe;
   - construye y publica la imagen Docker;
   - lee la task definition activa del servicio ECS;
   - registra una revision con la nueva imagen;
   - actualiza el servicio y espera estabilidad.

## Como probar

Backend local:

```powershell
cd backend
python -m pip install -r requirements.txt
$env:DATABASE_URL="sqlite:///./credibot_dev.db"
$env:DEBUG="false"
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

Health local:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

Docker local:

```powershell
docker build -t credibot-backend ./backend
docker run --rm -p 8000:8000 -e DATABASE_URL="sqlite:///./credibot_dev.db" credibot-backend
```

Produccion:

```text
https://api.midominio.com/health
```

## Estado actual de AWS

En esta maquina existe AWS CLI, pero no hay credenciales configuradas. Por eso no se crearon recursos ni se pudo verificar un ALB/ECS real desde esta sesion.

Pendiente para el equipo:

- Configurar credenciales temporales o usar una cuenta de setup para crear recursos iniciales.
- Crear ECS/ALB/Secrets Manager/RDS o Supabase.
- Crear el rol OIDC y guardar `AWS_ROLE_ARN` en GitHub.
- Configurar las variables de GitHub listadas arriba.
- Ejecutar el workflow desde `main`.
- Configurar dominio y certificado ACM.
- Actualizar Twilio con el webhook HTTPS final.

## Pendientes de produccion real

- Dominio propio y HTTPS en ALB.
- Separar ambientes staging/prod.
- Backups y monitoreo de PostgreSQL.
- Logs y alarmas CloudWatch.
- Rotacion de secretos.
- Autenticacion y roles para el dashboard.
- Validacion de firma de webhooks Twilio.
- Rate limiting y politicas de seguridad.
