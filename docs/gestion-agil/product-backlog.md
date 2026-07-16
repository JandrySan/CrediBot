# Product Backlog

Línea base consolidada: 15 de julio de 2026.

## Épicas

| ID | Épica | Resultado de negocio |
| --- | --- | --- |
| EP-01 | Atención por WhatsApp | Atender automáticamente una solicitud desde el canal autorizado |
| EP-02 | Precalificación explicable | Evaluar datos con reglas auditables y comunicar un resultado preliminar |
| EP-03 | Continuidad y atención humana | Conservar contexto por cliente y permitir escalamiento a un asesor |
| EP-04 | Experiencia y conocimiento | Comprender preguntas, audio y cambios de intención sin perder el objetivo |
| EP-05 | Operación segura | Probar, desplegar, proteger y observar el servicio |
| EP-06 | Evidencia académica | Mantener modelado, gestión y trazabilidad verificables |

## Historias priorizadas y estimadas

| ID | Épica | Historia resumida | MoSCoW | SP | Talla | Iteración | Estado |
| --- | --- | --- | --- | ---: | --- | --- | --- |
| US-01 | EP-01 | Intercambiar mensajes mediante webhook de WhatsApp | Must | 5 | M | 1 | Done |
| US-02 | EP-01 | Saludar e identificar la intención | Must | 3 | S | 1 | Done |
| US-03 | EP-01 | Recopilar nombre, monto, plazo e información financiera | Must | 8 | L | 1 | Done |
| US-04 | EP-03 | Aislar estado y mensajes por cliente | Must | 5 | M | 1 | Done |
| US-05 | EP-02 | Ejecutar reglas de precalificación | Must | 8 | L | 1 | Done |
| US-06 | EP-02 | Explicar y registrar el resultado | Must | 3 | S | 1 | Done |
| US-07 | EP-03 | Solicitar un asesor en cualquier momento | Must | 5 | M | 1 | Done |
| US-08 | EP-03 | Tomar, responder y cerrar conversaciones desde el panel | Must | 8 | L | 1 | Done |
| US-09 | EP-04 | Enviar y recibir audio por WhatsApp | Should | 8 | L | 1 | Done |
| US-10 | EP-04 | Consultar FAQs sin abandonar la solicitud | Should | 5 | M | 2 | Done |
| US-11 | EP-03 | Restaurar y depurar sesiones | Should | 5 | M | 2 | Done |
| US-12 | EP-05 | Validar y desplegar automáticamente | Must | 8 | L | 2 | Done |
| US-13 | EP-05 | Proteger dashboard, webhook y secretos | Must | 8 | L | 2 | Done |
| US-14 | EP-02 | Versionar productos, políticas y datos sintéticos | Should | 13 | XL | 2 | Done |
| US-15 | EP-04 | Adaptar el diálogo al orden y correcciones del usuario | Must | 13 | XL | 2 | Done |
| US-16 | EP-01 | Usar plantillas transaccionales versionadas | Must | 3 | S | 2 | Done |
| US-17 | EP-06 | Mantener modelos Mermaid vivos | Must | 8 | L | 2 | Done |
| US-18 | EP-06 | Mantener backlog, métricas y evidencia individual | Must | 8 | L | 2 | Done |
| US-19 | EP-05 | Incorporar alarmas operativas de CloudWatch | Could | 5 | M | Futuro | Product Backlog |
| US-20 | EP-05 | Separar ambientes staging y producción | Could | 8 | L | Futuro | Product Backlog |

## Criterios de aceptación

### US-01 — Mensajería WhatsApp

- Dado un mensaje válido del Sandbox, cuando Twilio invoca el webhook, entonces se
  devuelve TwiML y se registra el mensaje.
- La firma de Twilio se valida cuando la integración está habilitada.

### US-02 — Saludo e intención

- Un saludo obtiene una presentación breve y las opciones de crédito, información o asesor.
- Crédito, consulta y asesor se distinguen sin confundir nombres o frases comunes.

### US-03 — Captura de datos

- Se aceptan nombre, identificación, monto, plazo, ingresos, gastos y deudas.
- El bot pregunta únicamente los datos obligatorios que faltan y valida formatos.

### US-04 — Estado independiente

- Dos teléfonos distintos conservan clientes, conversaciones, mensajes y contextos separados.
- Una conversación cerrada no contamina una nueva sesión del mismo cliente.

### US-05 — Precalificación

- El motor usa tasa, plazo y límites de una política versionada.
- El resultado distingue `APTO` y `OBSERVADO` mediante códigos de razón auditables.

### US-06 — Resultado trazable

- La respuesta informa que el resultado es preliminar y no constituye aprobación definitiva.
- La solicitud, cuota, resultado y razones quedan disponibles en el dashboard.

### US-07 — Escalamiento

- “Asesor”, “humano”, “agente” y expresiones equivalentes activan `HANDOFF` desde cualquier etapa.
- Una petición de asesor detiene respuestas automáticas hasta que el caso sea cerrado.

### US-08 — Panel del asesor

- Un usuario autenticado puede tomar una conversación y responder al cliente por WhatsApp.
- Solo se guarda una respuesta manual después de que Twilio confirma su aceptación.
- Al cerrar el caso se registra la resolución y el siguiente mensaje inicia un flujo nuevo.

### US-09 — Audio

- Un audio entrante se transcribe y recorre el mismo flujo que un texto.
- El usuario puede solicitar respuestas en audio o volver a texto.

### US-10 — FAQs

- El bot responde preguntas de la base de conocimiento sin perder los campos recopilados.
- El panel permite cargar, listar y eliminar FAQs.

### US-11 — Sesiones

- Una sesión vigente se restaura y una sesión vencida se cierra según la configuración.
- Existe limpieza manual y automatizable de conversaciones abandonadas.

### US-12 — CI/CD

- Cada push o pull request ejecuta pruebas, análisis estático y build correspondientes.
- Un cambio aprobado en `main` despliega backend o frontend y comprueba salud pública.

### US-13 — Seguridad

- El dashboard usa JWT y roles; el webhook valida firma y aplica limitación de solicitudes.
- Los secretos productivos se inyectan desde AWS Secrets Manager y no se versionan.

### US-14 — Catálogo y políticas

- Productos, requisitos, reglas y versiones viven en PostgreSQL.
- El lote sintético es reproducible, identificable y no se confunde con datos reales.

### US-15 — Diálogo adaptable

- El usuario puede proporcionar varios datos en cualquier orden y corregirlos posteriormente.
- Una pregunta lateral se responde y luego se retoma el dato pendiente.
- El nombre proveniente del buró se confirma y una respuesta del flujo nunca se guarda como nombre.

### US-16 — Plantillas transaccionales

- Las confirmaciones tienen identificador, versión, variables requeridas y texto alternativo.
- El envío admite plantilla de Twilio mediante `ContentSid` cuando está configurada y usa texto
  versionado en el Sandbox.
- Existen pruebas del renderizado, variables inválidas y llamada a Twilio.

### US-17 — Modelado vivo

- El repositorio contiene Story Mapping y diagramas Mermaid de contexto, contenedores,
  dominio, estados y derivación humana.
- Cada diagrama enlaza componentes o estados que existen en el código.

### US-18 — Evidencia ágil

- Backlog, estimaciones, MoSCoW, dos iteraciones, ceremonias y cambio reestimado están documentados.
- Métricas y contribuciones se calculan desde Git y enlazan evidencia verificable.

### US-19 — Alarmas operativas

- Una alarma detecta errores o falta de tareas saludables y tiene un destinatario documentado.

### US-20 — Ambientes separados

- Staging y producción usan recursos, secretos y variables diferenciados.

## Dependencias

- US-05 depende de US-03.
- US-06 depende de US-05.
- US-08 depende de US-07 y US-01.
- US-15 depende de US-03, US-04 y US-05.
- US-16 depende de US-01.
- US-17 y US-18 documentan transversalmente el resto del backlog.
