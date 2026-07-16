# Máquina de estados conversacional

El diagrama refleja `backend/app/state_machine/states.py`. El flujo adaptable puede
rellenar varios campos en cualquier orden, pero el estado indica la siguiente necesidad
de mayor prioridad y conserva una transición auditable.

```mermaid
stateDiagram-v2
    [*] --> START
    START --> ASK_PRIVACY_CONSENT: iniciar precalificación
    START --> HANDOFF: pedir asesor
    START --> END: finalizar

    ASK_PRIVACY_CONSENT --> ASK_PRODUCT: acepta
    ASK_PRIVACY_CONSENT --> END: rechaza
    ASK_PRODUCT --> ASK_NATIONAL_ID
    ASK_NATIONAL_ID --> ASK_BUREAU_CONSENT
    ASK_BUREAU_CONSENT --> ASK_NAME: acepta o continúa sin consulta
    ASK_NAME --> ASK_AGE
    ASK_AGE --> ASK_EMPLOYMENT
    ASK_EMPLOYMENT --> ASK_EMPLOYMENT_TENURE
    ASK_EMPLOYMENT_TENURE --> ASK_AMOUNT
    ASK_AMOUNT --> ASK_TERM
    ASK_TERM --> ASK_INCOME
    ASK_INCOME --> ASK_EXPENSES
    ASK_EXPENSES --> ASK_DEBTS
    ASK_DEBTS --> ASK_PEP_STATUS
    ASK_PEP_STATUS --> SHOW_RESULT: datos suficientes
    SHOW_RESULT --> START: nueva simulación
    SHOW_RESULT --> HANDOFF: revisión humana
    SHOW_RESULT --> END: finalizar

    ASK_PRIVACY_CONSENT --> HANDOFF
    ASK_PRODUCT --> HANDOFF
    ASK_NATIONAL_ID --> HANDOFF
    ASK_BUREAU_CONSENT --> HANDOFF
    ASK_NAME --> HANDOFF
    ASK_AGE --> HANDOFF
    ASK_EMPLOYMENT --> HANDOFF
    ASK_EMPLOYMENT_TENURE --> HANDOFF
    ASK_AMOUNT --> HANDOFF
    ASK_TERM --> HANDOFF
    ASK_INCOME --> HANDOFF
    ASK_EXPENSES --> HANDOFF
    ASK_DEBTS --> HANDOFF
    ASK_PEP_STATUS --> HANDOFF

    HANDOFF --> END: asesor cierra
    END --> [*]
```

## Reglas de transición

- `HANDOFF` es alcanzable desde cualquier estado activo.
- Mientras una conversación permanece en `HANDOFF`, el bot no genera respuestas automáticas.
- El asesor solo puede responder manualmente en `HANDOFF`.
- Al cerrar, se registra resolución, la conversación pasa a `END` y el siguiente mensaje
  crea una conversación nueva.
- Una pregunta lateral no obliga a cambiar de estado: se responde y se conserva el campo pendiente.
- Una corrección puede hacer que la necesidad prioritaria vuelva a un campo anterior sin borrar
  los campos independientes que continúan siendo válidos.

## Resultado de negocio

`SHOW_RESULT` presenta `APTO` u `OBSERVADO`, cuota estimada y razones. La decisión formal
solo puede realizarla un asesor o una entidad autorizada fuera del alcance del MVP.
