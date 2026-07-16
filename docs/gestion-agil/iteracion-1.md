# Iteración 1 — MVP extremo a extremo

Periodo observado: 6–9 de julio de 2026, UTC-5.  
Acta consolidada: 15 de julio de 2026.  
Evidencia base: 19 commits y pull request #1.

## Planning

Objetivo: permitir que un cliente complete una precalificación por WhatsApp, conservar
su conversación y solicitar atención humana desde un dashboard.

Historias comprometidas: US-01 a US-09.  
Estimación total reconstruida mediante Planning Poker: 53 SP.

| Historia | SP | Responsable principal verificable | Evidencia de selección |
| --- | ---: | --- | --- |
| US-01, US-02 | 8 | JandrySan / CrlsDuty | Backend inicial e integración Twilio |
| US-03, US-04 | 13 | JandrySan / diegocalva04 | Repositorios, estados y flujo funcional |
| US-05, US-06 | 11 | JandrySan / diegocalva04 | Reglas, IA y resultado crediticio |
| US-07, US-08 | 13 | JandrySan / diegocalva04 | Dashboard y handoff |
| US-09 | 8 | diegocalva04 | Audio entrante y saliente |

Riesgos identificados a partir del trabajo observado:

- Dependencia de credenciales y sesión activa del Twilio Sandbox.
- Posible mezcla de estado si la conversación no se relaciona con un teléfono único.
- Respuestas de IA no auditables si las reglas quedan dentro del prompt.
- Integración frontend/backend sensible a URL y CORS.

## Seguimiento diario reconstruido

| Fecha | Incremento verificable | Decisión o ajuste |
| --- | --- | --- |
| 6 de julio | Base de datos, modelos, repositorios, conversación e IA | Separar persistencia, flujo y análisis |
| 7 de julio | React/MUI, dashboard, WebSocket, toma y respuesta de casos | Hacer visible la operación humana |
| 8 de julio | Correcciones de integración, Twilio, reglas y flujo funcional | Priorizar demostración extremo a extremo |
| 9 de julio | Audio, handoff sin respuesta automática y cierre manual | Evitar que bot y asesor respondan simultáneamente |

## Revisión

Incremento demostrable al cierre:

1. Mensaje del Sandbox recibido mediante webhook.
2. Captura de datos y aplicación de reglas de negocio.
3. Respuesta por texto y audio.
4. Conversación visible en el dashboard.
5. Derivación a humano y cierre manual.

Evidencia:

- Pull request #1, fusionado el 8 de julio a las 20:03 UTC-5.
- Commits `de297f1`, `1ca2531`, `8bbaf7a` y `e02d6ca`.
- README e instrucciones de integración actualizadas durante la iteración.

Resultado: 9 historias terminadas, 53/53 SP del alcance reconstruido.

## Retrospectiva de la iteración

Esta retrospectiva fue consolidada el 15 de julio a partir de los cambios y defectos
observados; debe ser validada por el equipo en el pull request documental.

### Mantener

- Separación entre reglas deterministas e interpretación con IA.
- Entrega incremental que permitió probar WhatsApp antes de completar el dashboard.
- Handoff explícito para impedir respuestas simultáneas.

### Mejorar

- Crear pruebas y CI desde el inicio, no después del primer incremento.
- Usar ramas breves y pull requests para todos los cambios relevantes.
- Definir variables y secretos antes de integrar servicios externos.

### Acciones incorporadas en la iteración 2

- Formalizar máquina de estados y sesiones.
- Agregar pruebas automatizadas y CI/CD.
- Modularizar el backend.
- Reforzar seguridad y configuración productiva.

## Participación verificable

| Integrante Git | Commits en el periodo |
| --- | ---: |
| JandrySan | 10 |
| CrlsDuty | 4 |
| diegocalva04 | 4 |
| FranmVeera | 1 |

Estas cifras prueban actividad Git; no equivalen por sí solas a esfuerzo ni calidad.
