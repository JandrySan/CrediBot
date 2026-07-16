# Guion de demostración — CrediBot

Duración objetivo: 12 minutos.  
Entorno: Twilio Sandbox, frontend CloudFront y backend AWS/Supabase.

## Preparación previa

1. Confirmar que `https://d30z3dsmpm7ctx.cloudfront.net` abre correctamente.
2. Confirmar que `/api/health` devuelve `{"status":"ok"}`.
3. Verificar que el teléfono de demostración esté unido al Sandbox.
4. Abrir el dashboard e iniciar sesión como asesor.
5. Mantener abierta la página de conversaciones.
6. Usar una cédula sintética, nunca datos reales.
7. Tener preparada la ejecución exitosa más reciente de GitHub Actions.

## Recorrido de 10–15 minutos

### 0:00–1:00 — Problema y alcance

- Una entidad necesita atender consultas y filtrar solicitudes iniciales por WhatsApp.
- CrediBot orienta y precalifica; no aprueba ni desembolsa automáticamente.
- Twilio Sandbox está permitido para el entorno académico.

### 1:00–2:00 — Arquitectura

- Mostrar los diagramas de contexto y contenedores.
- Explicar WhatsApp → Twilio → CloudFront → ECS/FastAPI → Supabase/Groq.
- Aclarar que la IA interpreta y las reglas deterministas deciden el resultado preliminar.

### 2:00–6:00 — Conversación adaptable

Secuencia sugerida:

1. `Hola, quiero saber los requisitos de un crédito.`
2. `Quiero continuar. Gano 2000, gasto 600 y necesito 5000 a 24 meses.`
3. Aceptar privacidad.
4. Elegir consumo personal.
5. Usar cédula sintética `1111111111` para un escenario favorable.
6. Autorizar consulta de buró.
7. Confirmar o corregir el nombre.
8. Completar únicamente los campos faltantes.
9. Preguntar lateralmente `¿Qué tasa están usando?` y comprobar que retoma el flujo.
10. Corregir `Mejor quiero 36 meses` y mostrar el nuevo cálculo.

Puntos a explicar:

- Estado separado por teléfono.
- Slots con procedencia y confirmación.
- Consentimientos separados.
- Resultado preliminar y explicable.

### 6:00–8:30 — Derivación humana

1. Escribir `Quiero hablar con una persona`.
2. Mostrar la confirmación transaccional.
3. Comprobar que la conversación aparece en `HANDOFF`.
4. Tomarla desde el panel.
5. Responder desde el dashboard y observar el mensaje en WhatsApp.
6. Cerrar con resolución y explicar que un nuevo mensaje crea otra conversación.

### 8:30–9:30 — Registro y analítica

- Mostrar mensajes, datos de solicitud, estado y resultado.
- Mostrar métricas de conversaciones, precalificaciones y derivación.
- Mencionar FAQ/RAG y limpieza de sesiones.

### 9:30–10:30 — Calidad y DevOps

- Mostrar GitHub Actions: lint, Mypy, pruebas, build y despliegues.
- Mostrar Docker, ECS Fargate, S3/CloudFront y Supabase.
- Mencionar Sonar y cobertura.

### 10:30–11:30 — Gestión y modelado

- Mostrar GitHub Project, Product Backlog y las dos iteraciones.
- Enseñar Story Mapping, máquina de estados y CR-001 reestimado de 8 a 13 SP.
- Mostrar burndown, velocidad y contribuciones.

### 11:30–12:00 — Cierre

- Logro: MVP funcional, accesible, probado y superior al mínimo.
- Límite: resultado informativo con revisión humana.
- Próximos pasos: alarmas CloudWatch y staging separado.

## Plan alterno si falla un servicio externo

- Si Twilio expira: mostrar pruebas automatizadas, registros previos y ejecutar el flujo local.
- Si Groq no responde: demostrar fallback determinista.
- Si CloudFront falla: usar frontend local contra backend local.
- Si el buró no encuentra cédula: usar perfiles sintéticos documentados.
- Nunca editar producción durante la demostración.

## Distribución sugerida por integrante

| Bloque | Responsable sugerido |
| --- | --- |
| Problema y gestión | Product owner / facilitador |
| Conversación y reglas | Backend/IA |
| Dashboard y experiencia | Frontend |
| DevOps, calidad y cierre | DevOps/backend |

La asignación definitiva debe acordarla el equipo; el historial Git permite que cada
persona presente un área en la que tiene contribución verificable.
