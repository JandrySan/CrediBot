# Retrospectiva final del equipo

Fecha de consolidación: 15 de julio de 2026.  
Validación colectiva: aprobación pendiente mediante pull request.

## Resultado frente al objetivo

CrediBot permite realizar una precalificación informativa por WhatsApp, interpretar texto
y audio, consultar reglas y datos sintéticos, conservar estado por usuario y escalar a un
asesor que opera desde un dashboard. El sistema está desplegado y cuenta con CI/CD.

## Lo que funcionó bien

- Se consiguió un recorrido extremo a extremo temprano y se mejoró incrementalmente.
- La IA se limitó a interpretación y redacción; la decisión se mantuvo en reglas auditables.
- El handoff no es simulado: el asesor puede tomar, responder y cerrar el caso.
- El equipo incorporó audio, FAQs, analítica y conversación adaptable sobre el MVP.
- La automatización detectó problemas antes del despliegue y dejó ejecuciones reproducibles.
- Los datos sintéticos permiten demostrar perfiles favorables y observados sin usar personas reales.

## Lo que no funcionó bien

- Backlog y tablero no se mantuvieron como fuente primaria desde el primer día.
- La mayoría de los cambios entraron directamente a `main`; hubo solo dos pull requests.
- La documentación de ceremonias y estimaciones se consolidó al cierre.
- La primera arquitectura concentró demasiadas responsabilidades en el orquestador y dashboard.
- El flujo secuencial inicial no manejaba bien interrupciones, correcciones o nombres sugeridos.
- La observabilidad tiene logs, pero aún carece de alarmas y objetivos de servicio documentados.

## Lecciones aprendidas

1. Un chatbot orientado a tareas necesita estado auditable y también flexibilidad por campos.
2. La IA no debe ser la única fuente de reglas en un proceso financiero.
3. Integrar servicios externos exige validar credenciales, errores de entrega y permisos desde CI/CD.
4. La evidencia ágil debe producirse durante el trabajo; reconstruirla es posible, pero menos precisa.
5. Un despliegue accesible y una demo repetible valen más que muchas funciones no verificadas.
6. Las pruebas con lenguaje real de usuarios descubren fallos que las rutas felices no muestran.

## Start, Stop, Continue

### Start

- Crear historias y criterios antes de escribir código.
- Actualizar el tablero al comenzar y terminar cada tarea.
- Medir cycle time desde GitHub Projects.
- Exigir pull request y CI para cambios relevantes.
- Definir alarmas y staging antes del siguiente despliegue productivo.

### Stop

- Hacer cambios grandes directamente en `main`.
- Tratar commits como sustituto de planificación.
- Permitir que la IA invente o modifique reglas comerciales.
- Repetir información sensible innecesariamente en respuestas o logs.

### Continue

- Mantener reglas versionadas y explicables.
- Probar correcciones reportadas por usuarios.
- Realizar commits pequeños y descriptivos.
- Conservar documentación, diagramas y código en el mismo repositorio.

## Métricas de cierre

- Velocidad: 53 SP y 71 SP; media de 62 SP.
- Actividad: 80 commits en los dos cortes funcionales.
- Cobertura backend previa al cierre: 66,6 % de líneas.
- Pipeline: cuatro workflows funcionales.
- Despliegue: frontend y API accesibles por CloudFront.
- Integrantes con evidencia Git: cuatro.

## Acciones de mejora priorizadas

| Acción | Responsable sugerido | Prioridad | Historia |
| --- | --- | --- | --- |
| Configurar alarma de salud/errores | DevOps | Should | US-19 |
| Separar staging y producción | DevOps/backend | Could | US-20 |
| Mantener GitHub Project en tiempo real | Todo el equipo | Must | US-18 |
| Aumentar pruebas frontend | Frontend | Should | Backlog futuro |
| Registrar SLA de atención humana | Producto/operación | Should | Backlog futuro |

## Ratificación

La aprobación del pull request de cierre significa que cada integrante revisó las
atribuciones, las lecciones y la reconstrucción cronológica. Cualquier desacuerdo debe
corregirse antes de fusionar; no se debe firmar evidencia con la que el equipo no esté de acuerdo.
