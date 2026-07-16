# Arquitectura como código

## 1. Diagrama de contexto

```mermaid
flowchart LR
    Cliente[Cliente por WhatsApp]
    Asesor[Asesor de crédito]
    Admin[Administrador]
    CrediBot[CrediBot<br/>precalificación y atención]
    Twilio[Twilio WhatsApp Sandbox]
    Groq[Groq IA y STT]
    AWS[AWS]
    Supabase[Supabase PostgreSQL]

    Cliente <--> Twilio
    Twilio <--> CrediBot
    Asesor <--> CrediBot
    Admin <--> CrediBot
    CrediBot --> Groq
    CrediBot <--> Supabase
    CrediBot --> AWS
```

### Responsabilidades externas

- El cliente conversa, autoriza datos, corrige información y solicita un asesor.
- El asesor toma el caso, responde y registra la resolución.
- Twilio entrega webhooks y mensajes dentro del entorno académico permitido.
- Groq clasifica intención, extrae propuestas, redacta y transcribe; no decide el crédito.
- Supabase conserva la fuente transaccional y de reglas.
- AWS aloja y distribuye la aplicación.

## 2. Diagrama de contenedores

```mermaid
flowchart TB
    subgraph Canal[Canal externo]
        WA[WhatsApp]
        TW[Twilio Sandbox]
        WA <--> TW
    end

    subgraph AWS[AWS]
        CF[CloudFront<br/>entrada pública]
        S3[S3<br/>React estático]
        ALB[Application Load Balancer]
        ECS[ECS Fargate<br/>FastAPI]
        ECR[ECR<br/>imagen Docker]
        SM[Secrets Manager]
        CW[CloudWatch Logs]
        CF --> S3
        CF --> ALB
        ALB --> ECS
        ECR --> ECS
        SM --> ECS
        ECS --> CW
    end

    Browser[Navegador del asesor] --> CF
    TW <--> CF
    ECS <--> DB[(Supabase PostgreSQL)]
    ECS <--> AI[Groq LLM / STT]
    GHA[GitHub Actions] --> ECR
    GHA --> ECS
    GHA --> S3
    GHA --> CF
```

## 3. Componentes principales del backend

```mermaid
flowchart LR
    API[API y webhooks]
    SEC[Seguridad]
    ORQ[Orquestador conversacional]
    FLOW[Flujo adaptable y slots]
    STATE[Máquina de estados]
    TOOLS[Tools / FAQ / IA]
    RULES[Motor crediticio]
    DASH[Servicios del dashboard]
    REPO[Repositorios]
    ORM[Modelos SQLAlchemy]

    API --> SEC
    API --> ORQ
    API --> DASH
    ORQ --> FLOW
    ORQ --> STATE
    ORQ --> TOOLS
    ORQ --> RULES
    ORQ --> REPO
    DASH --> REPO
    REPO --> ORM
```

## Decisiones arquitectónicas

1. La IA interpreta lenguaje natural, pero las reglas crediticias son deterministas.
2. El teléfono identifica al cliente y cada conversación tiene contexto propio.
3. El handoff cambia control operativo; no es solo una etiqueta visual.
4. CloudFront ofrece un único origen público para frontend, API, webhook y audio.
5. Los secretos no forman parte de la imagen ni del repositorio.
6. Las políticas se versionan para poder explicar con qué reglas se obtuvo un resultado.
