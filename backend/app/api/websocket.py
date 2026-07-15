from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect

from app.config.settings import settings
from app.security.auth import decode_access_token
from app.services.websocket.connection_manager import manager

router = APIRouter(tags=["WebSocket"])


@router.websocket("/ws/dashboard")
async def dashboard_websocket(websocket: WebSocket):
    if settings.DASHBOARD_AUTH_ENABLED:
        try:
            decode_access_token(websocket.query_params.get("token", ""))
        except HTTPException:
            await websocket.close(code=1008, reason="Autenticacion requerida")
            return

    await manager.connect(websocket)

    try:
        while True:
            await websocket.receive_text()

    except WebSocketDisconnect:
        manager.disconnect(websocket)
