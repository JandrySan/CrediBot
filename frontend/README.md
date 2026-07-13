# CrediBot Frontend

Dashboard web para asesores de CrediBot.

## Stack

- React
- TypeScript
- Vite
- Material UI
- React Query
- WebSocket nativo para eventos en tiempo real

## Rutas

- `/`: panel de conversaciones.
- `/faqs`: administracion de FAQs.

## Variables

Archivo local:

```text
frontend/.env
```

Ejemplo:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
VITE_WS_BASE_URL=ws://127.0.0.1:8000
```

Si `VITE_WS_BASE_URL` se omite, se deriva desde `VITE_API_BASE_URL`.

En produccion, el build puede quedar sin `VITE_API_BASE_URL`; en ese caso usa
el mismo origen del navegador. Actualmente CloudFront enruta:

- `/api/*` al backend.
- `/ws/*` al backend.
- `/webhook/*` al backend.
- El resto al sitio estatico en S3.

URL productiva actual:

```text
https://d30z3dsmpm7ctx.cloudfront.net
```

## Comandos

Instalar dependencias:

```powershell
npm install
```

Desarrollo local:

```powershell
npm run dev
```

Validar lint:

```powershell
npm run lint
```

Build productivo:

```powershell
npm run build
```

## Funcionalidades

- Estadisticas generales.
- Lista de conversaciones.
- Panel con cedula, nombre, monto, plazo, ingreso y resultado.
- Chat de conversacion.
- Toma de conversacion por asesor.
- Respuesta manual por WhatsApp.
- Cierre de conversaciones.
- Limpieza manual de conversaciones expiradas.
- Administracion de FAQs.
- Actualizacion en tiempo real por WebSocket.
