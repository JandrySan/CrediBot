# Modelado ágil de CrediBot

Fecha de actualización: 15 de julio de 2026.

Los modelos usan Mermaid.js y viven junto al código para poder revisarse en los mismos
pull requests. El alcance responde a la opción C del proyecto académico.

## Índice

- [Story Mapping](story-mapping.md)
- [Contexto y contenedores](arquitectura.md)
- [Dominio crediticio](dominio.md)
- [Máquina de estados](maquina-estados.md)
- [Derivación bot–humano](derivacion-humana.md)

## Correspondencia con la guía

| Exigencia | Artefacto |
| --- | --- |
| Story Mapping | `story-mapping.md` |
| Diagrama de contexto | `arquitectura.md`, sección 1 |
| Diagrama de contenedores | `arquitectura.md`, sección 2 |
| Modelado de dominio | `dominio.md` |
| Máquina de estados | `maquina-estados.md` |
| Derivación humano–bot | `derivacion-humana.md` |

## Regla de mantenimiento

Todo cambio que agregue un contenedor, una entidad persistente, un estado o una transición
debe actualizar el diagrama correspondiente dentro del mismo pull request.
