# Evidencia de contribución individual

Corte: `origin/main` en `f2d59d7`, 15 de julio de 2026.  
Fuente reproducible: `git shortlog -sne --all` y `git log --author=<usuario>`.

## Resumen cuantitativo

| Identidad Git | Commits | Áreas verificables |
| --- | ---: | --- |
| diegocalva04 | 53 | CI/CD AWS, Supabase, seguridad, refactor, dominio crediticio, dataset y flujo adaptable |
| FranmVeera | 15 | FAQ/RAG, sesiones, frontend de FAQs, preferencias, analítica y mejoras conversacionales |
| JandrySan | 10 | Fundación backend, modelos, orquestación IA, frontend, dashboard, WebSocket y Twilio |
| CrlsDuty | 8 | Documentación inicial, integración Twilio/ngrok, PR #1, máquina de estados, tools y correcciones |

Dos correos/identidades de CrlsDuty se consolidan como la misma persona; Git muestra 7 + 1 commits.
Los commits posteriores del cierre documental se atribuyen por Git y no alteran este corte base.

## Evidencia cualitativa

### JandrySan

- `e670bfc`: base de datos y modelos.
- `1fec240`: conversación, repositorios y solicitudes.
- `f46f640` y `a10c8bc`: IA, extracción y orquestación.
- `86e3cfc`, `61c9f0d` y `430de3d`: frontend, dashboard y WebSocket.
- `30e213e` y `9e619e2`: atención humana y envío Twilio.

### CrlsDuty

- `a5174a8`: Twilio y ngrok funcional.
- `4837ce8` y PR #1: correcciones de arranque e integración.
- `68c7500`: máquina de estados y tools.
- `bad7564`: intención de consulta sin interrumpir el flujo.
- `f42e9c6`: corrección de chats duplicados.

### FranmVeera

- `55a765d` y `ad1abfe`: FAQ/RAG en backend y frontend.
- `0a3c0ad`: sesiones, restauración y limpieza.
- `6e2cc4a`: preferencia de audio o texto.
- `4889626`: páginas de analítica y configuración.
- `518baa6`, `bf04007`, `67ce0da` y `c5d4544`: saludo, nombres, explicación y calidad.

### diegocalva04

- `06fdfdc`, `4921d6a` y posteriores: CI/CD, ECS, ECR, S3 y CloudFront.
- `54c9be5`: modularización y preparación productiva.
- `6dbd0cb` a `76a0fd6`: investigación, dominio, políticas y motor crediticio.
- `cd338e5` y `7121490`: dataset sintético masivo y documentación.
- `ed8f389` a `cc8846e`: memoria por campos, diálogo adaptable y correcciones de nombre.
- `3974b29`: respuesta del asesor desde el panel.

## Interpretación responsable

El número de commits no mide por sí solo el esfuerzo. Una revisión, prueba manual,
investigación o decisión puede aportar valor sin generar muchos commits. La tabla se usa
como evidencia individual mínima exigida y se complementa con áreas y cambios concretos.

## Comandos de reproducción

```powershell
git shortlog -sne --all
git log --author=JandrySan --oneline
git log --author=CrlsDuty --oneline
git log --author=FranmVeera --oneline
git log --author=diegocalva04 --oneline
```
