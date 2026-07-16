# Derivación bot–humano

## Secuencia principal

```mermaid
sequenceDiagram
    autonumber
    participant U as Usuario WhatsApp
    participant T as Twilio Sandbox
    participant B as Backend CrediBot
    participant D as PostgreSQL
    participant P as Dashboard
    participant A as Asesor

    U->>T: “Quiero hablar con una persona”
    T->>B: Webhook firmado
    B->>D: Registrar mensaje y transición a HANDOFF
    B-->>T: Confirmación de derivación
    T-->>U: Caso enviado a un asesor
    B-->>P: Evento WebSocket / actualización
    A->>P: Tomar conversación
    P->>B: POST tomar
    B->>D: Mantener HANDOFF y asignar control humano
    B->>T: Notificar que el asesor tomó el caso
    T-->>U: Confirmación transaccional
    A->>P: Escribir respuesta
    P->>B: POST responder
    B->>T: Enviar WhatsApp
    T-->>U: Mensaje del asesor
    B->>D: Guardar solo si Twilio acepta el envío
    A->>P: Cerrar con resolución
    P->>B: POST cerrar
    B->>D: Estado END y resolución
```

## Reglas de control

1. La intención de asesor se evalúa antes de continuar el flujo automático.
2. En `HANDOFF`, cualquier mensaje nuevo se registra, pero el bot permanece silencioso.
3. El panel exige autenticación y el rol adecuado.
4. Una respuesta fallida de Twilio no se registra como entregada.
5. El asesor elige una resolución y puede añadir una nota.
6. Al cerrar, el siguiente contacto vuelve a `START` con una conversación nueva.

## Casos alternos

```mermaid
flowchart TD
    A[Solicitud de asesor] --> B{¿Conversación cerrada?}
    B -- Sí --> C[Crear conversación activa]
    B -- No --> D[Usar conversación abierta]
    C --> E[Transicionar a HANDOFF]
    D --> E
    E --> F{¿Cliente existe?}
    F -- No --> G[Informar error operativo]
    F -- Sí --> H[Notificar por Twilio]
    H --> I{¿Twilio acepta?}
    I -- No --> J[Mostrar error real al asesor]
    I -- Sí --> K[Registrar mensaje y continuar]
```

La ruta humana está disponible mediante lenguaje natural, no depende de completar primero
la precalificación y cumple la exigencia de escalamiento permanente del caso académico.
