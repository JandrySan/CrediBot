# Gestión ágil de CrediBot

Fecha de consolidación documental: 15 de julio de 2026.

## Propósito

Este directorio reúne la evidencia solicitada para la planificación y gestión ágil de
CrediBot: Product Backlog, estimaciones, priorización, dos iteraciones, ceremonias,
cambio de requisito, métricas, retrospectiva y contribución individual.

## Integridad y trazabilidad de las fechas

Las fechas de trabajo se obtuvieron del historial Git, pull requests y ejecuciones de
GitHub Actions. Los documentos se consolidaron el 15 de julio de 2026; por tanto, no
pretenden que una acta haya sido escrita antes de esa fecha. Cuando una decisión se
reconstruye a partir de evidencia técnica se indica expresamente.

Los cortes cronológicos son:

| Iteración | Periodo UTC-5 | Objetivo | Evidencia verificable |
| --- | --- | --- | --- |
| Iteración 1 | 6–9 de julio de 2026 | MVP funcional extremo a extremo | 19 commits, PR #1, integración Twilio y dashboard |
| Iteración 2 | 12–15 de julio de 2026 | Robustecer, desplegar y adaptar el producto | 61 commits hasta `f2d59d7`, CI/CD y despliegues AWS |

La revisión formal por parte del equipo debe quedar registrada mediante aprobación del
pull request que incorpora esta documentación. Esa aprobación constituye la validación
colectiva de la reconstrucción y evita atribuir asistencia o acuerdos no verificables.

## Método de trabajo

- Marco: Scrum adaptado a iteraciones académicas cortas.
- Estimación: Planning Poker con escala Fibonacci `1, 2, 3, 5, 8, 13`.
- Equivalencia visual: XS = 1, S = 2–3, M = 5, L = 8, XL = 13.
- Priorización: MoSCoW.
- Tablero: [GitHub Projects público](https://github.com/users/diegocalva04/projects/1),
  con vistas `Product Backlog` y `Tablero Kanban`; sus campos ágiles usan los estados
  `Product Backlog`, `Ready`, `In progress`, `In review` y `Done`.
- Definición de terminado: criterios aceptados, pruebas pertinentes aprobadas,
  revisión de código, documentación actualizada y CI en verde.

## Índice de evidencias

- [Product Backlog](product-backlog.md)
- [Tablero de GitHub Projects](tablero-github.md)
- [Iteración 1](iteracion-1.md)
- [Iteración 2](iteracion-2.md)
- [Cambio de requisito CR-001](cambio-requisito-cr-001.md)
- [Métricas](metricas.md)
- [Retrospectiva final](retrospectiva-final.md)
- [Contribuciones individuales](contribuciones.md)
- [Estrategia de ramas](estrategia-ramas.md)
- [Guion de demostración](../presentacion/guion-demo.md)
- [Modelado ágil](../modelado/README.md)

## Definición de listo

Una historia puede entrar a una iteración cuando tiene valor de negocio explícito,
criterios de aceptación comprobables, prioridad MoSCoW, estimación y dependencias
identificadas.

## Definición de terminado

1. El comportamiento cumple todos los criterios de aceptación.
2. Las pruebas automatizadas relacionadas pasan.
3. Ruff, Mypy, lint y build pasan cuando corresponda.
4. No se incorporan secretos al repositorio.
5. La documentación y los diagramas afectados están actualizados.
6. El cambio está asociado a una historia y cuenta con evidencia Git.
7. La rama se integra mediante pull request con CI aprobado.
