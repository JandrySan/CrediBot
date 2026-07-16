# Iteración 2 — Robustecimiento, despliegue y adaptación

Periodo observado: 12–15 de julio de 2026, UTC-5.  
Acta consolidada: 15 de julio de 2026.  
Corte funcional para métricas: commit `f2d59d7`.

## Planning

Objetivo: convertir el MVP en un servicio accesible, probado, seguro, explicable y
adaptable, con información suficiente para operación y evaluación académica.

Historias comprometidas: US-10 a US-18.  
Estimación total: 71 SP.

| Historia | SP | Foco | Responsable principal verificable |
| --- | ---: | --- | --- |
| US-10 | 5 | FAQ/RAG | FranmVeera / CrlsDuty |
| US-11 | 5 | Sesiones | FranmVeera |
| US-12 | 8 | CI/CD y AWS | diegocalva04 |
| US-13 | 8 | Seguridad y calidad | diegocalva04 |
| US-14 | 13 | Dominio crediticio y datos | diegocalva04 |
| US-15 | 13 | Conversación adaptable | diegocalva04 / FranmVeera |
| US-16 | 3 | Plantillas transaccionales | cierre académico |
| US-17 | 8 | Modelado como código | cierre académico |
| US-18 | 8 | Evidencia ágil | cierre académico |

## Seguimiento diario reconstruido

| Fecha | Incremento verificable | Decisión o ajuste |
| --- | --- | --- |
| 12 de julio | Máquina de estados, tools, FAQ, sesiones, CI/CD, preferencia audio/text | Reducir acoplamiento y preparar producción |
| 13 de julio | Supabase, central simulada, CloudFront, dashboard analítico y correcciones Twilio | Priorizar un despliegue demostrable y trazable |
| 14 de julio | Sin commits en `main` | Mantener el corte de evidencia sin atribuir trabajo no verificable |
| 15 de julio | Refactor, seguridad, políticas, dataset, motor versionado y diálogo adaptable | Gestionar CR-001 y cerrar calidad/documentación |

## Revisión

Incremento demostrable:

1. Frontend público en CloudFront y backend en ECS Fargate.
2. PostgreSQL de Supabase con productos, políticas y perfiles sintéticos.
3. CI de backend y frontend; CD de backend y frontend.
4. Dashboard con autenticación, métricas y atención humana.
5. Conversación adaptable con preguntas laterales y correcciones.
6. Validación de firma Twilio, rate limiting y secretos en AWS.
7. Story Mapping, diagramas como código y evidencia ágil.
8. Plantillas transaccionales versionadas y probadas.

Evidencia técnica:

- 61 commits entre el 12 y el corte `f2d59d7`.
- Ejecuciones exitosas de validación backend/frontend y despliegue AWS.
- `https://d30z3dsmpm7ctx.cloudfront.net` y `/api/health` responden HTTP 200.
- Commits representativos: `68a765d`, `55a765d`, `06fdfdc`, `4921d6a`,
  `54c9be5`, `76a0fd6`, `b8c97af`, `924f173` y `c5d4544`.

## Retrospectiva de la iteración

### Mantener

- Calidad automática antes de desplegar.
- Reglas crediticias versionadas fuera de la IA.
- Pruebas con datos sintéticos reproducibles.
- Respuesta a retroalimentación real del flujo conversacional.

### Mejorar

- Reducir commits directos a `main` y aumentar revisiones por pull request.
- Incorporar tablero e historias desde el inicio del siguiente proyecto.
- Separar staging y producción.
- Agregar alarmas, trazas correlacionadas y objetivos de servicio.

### Acciones siguientes

- US-19: alarma operativa de CloudWatch.
- US-20: ambiente de staging separado.
- Usar el tablero como fuente primaria de métricas, no reconstruirlas desde Git.

## Participación verificable al corte

| Integrante Git | Commits en el periodo |
| --- | ---: |
| diegocalva04 | 43 |
| FranmVeera | 14 |
| CrlsDuty | 4 |

Resultado previsto al cerrar este pull request: 71/71 SP. Los commits documentales y
de plantillas se registran después del corte funcional para que la cifra sea reproducible.
