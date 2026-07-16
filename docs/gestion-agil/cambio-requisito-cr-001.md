# CR-001 — Conversación adaptable y comprensible

Estado: implementado y pendiente de ratificación del equipo en pull request.  
Solicitud observada: 15 de julio de 2026.  
Historias afectadas: US-02, US-03, US-05, US-06 y US-15.

## 1. Requisito original

El MVP solicitaba un flujo estructurado que recopilara nombre, monto y plazo paso a paso.
La primera implementación representaba este recorrido principalmente mediante una máquina
de estados secuencial.

## 2. Retroalimentación que originó el cambio

Durante pruebas manuales se observaron estos problemas:

- El usuario quería preguntar requisitos antes de iniciar la solicitud.
- Una pregunta lateral podía romper o reiniciar el avance.
- El nombre recuperado del buró se presentaba sin una confirmación suficientemente clara.
- Frases como “simulador de crédito” podían terminar almacenadas como nombre.
- El resultado repetía demasiados datos y razones técnicas.
- Después del resultado no quedaban claras las acciones disponibles.

La evidencia se conserva en los casos de prueba agregados y en los commits de corrección
del 15 de julio.

## 3. Nuevo requisito

Como solicitante, quiero conversar en lenguaje natural, proporcionar información en cualquier
orden, interrumpir con preguntas y corregir datos, para completar una precalificación sin
quedar atrapado en una secuencia rígida ni recibir respuestas incoherentes.

## 4. Análisis de impacto

| Área | Impacto |
| --- | --- |
| Conversación | Incorporar contexto por slots independiente del estado lineal |
| Persistencia | Guardar valor, estado, fuente y confianza por campo |
| IA | Usarla para intención y extracción propuesta, nunca como fuente final de reglas |
| Reglas | Invalidar y recalcular únicamente resultados dependientes de un dato corregido |
| Experiencia | Preguntar solo el dato faltante de mayor valor y resumir respuestas |
| Buró | Confirmar el nombre sugerido antes de asumirlo como nombre del usuario |
| Pruebas | Cubrir orden flexible, preguntas laterales, correcciones y falsas extracciones |
| Modelado | Diferenciar estado conversacional y estado de cada slot |

## 5. Estimación y reestimación

La estimación se consolidó al formalizar el cambio y debe ser ratificada por el equipo:

| Momento | Alcance entendido | Estimación |
| --- | --- | ---: |
| Inicial | Mejorar textos y permitir responder una pregunta lateral | 8 SP |
| Después del análisis | Slots persistentes, procedencia, confirmación, invalidación, nuevo motor y pruebas | 13 SP |

Motivo de la reestimación: el defecto no era únicamente de redacción; requería modificar
memoria conversacional, persistencia, dependencias del cálculo y estrategia de pruebas.
La estimación aumenta 5 SP y conserva prioridad **Must** porque afecta la comprensión y
la confiabilidad del MVP.

## 6. Criterios de aceptación

1. Se pueden proporcionar varios datos válidos en un solo mensaje y en cualquier orden.
2. El bot responde requisitos o condiciones y retoma el campo pendiente.
3. Una corrección actualiza el slot, conserva procedencia e invalida el resultado dependiente.
4. El nombre del buró se confirma y puede rechazarse sin reiniciar la solicitud.
5. Expresiones de producto o preferencia de audio no se almacenan como nombres.
6. El resultado es breve, explicable y muestra próximos pasos.
7. Pedir un asesor funciona antes, durante y después de la precalificación.

## 7. Evidencia de implementación

| Evidencia | Aporte |
| --- | --- |
| `ed8f389` | Memoria por campos |
| `b8c97af` | Diálogo adaptable |
| `8c71419` | Confirmación y protección del nombre |
| `924f173` | Simplificación de la precalificación |
| `cc8846e` | Evitar que respuestas del flujo se conviertan en nombre |
| `67ce0da` | Explicación y respuestas posteriores al resultado |
| `c5d4544` | Correcciones detectadas por calidad automática |
| `fac926d` | Handoff permanente con confirmación transaccional |

Pruebas relacionadas:

- `test_adaptive_credit_flow.py`
- `test_adaptive_name_confirmation.py`
- `test_orchestrator_response_style.py`
- `test_whatsapp_transactional_templates.py`

## 8. Aceptación del cambio

El cambio se considera técnicamente aceptado cuando CI está en verde. La aprobación del
pull request por integrantes del equipo ratifica alcance, estimación y evidencia documental.
