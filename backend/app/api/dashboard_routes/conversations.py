from fastapi import APIRouter, Depends, Form
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.dashboard import (
    ActionResponse,
    CleanupResponse,
    ConversationMessage,
    ConversationSummary,
)
from app.security.auth import require_roles
from app.services.dashboard.conversation_service import DashboardConversationService
from app.services.dashboard.query_service import DashboardQueryService
from app.services.websocket.connection_manager import manager

router = APIRouter(prefix="/conversations")


@router.get("", response_model=list[ConversationSummary])
def get_conversations(db: Session = Depends(get_db)) -> list[ConversationSummary]:
    return DashboardQueryService(db).get_conversations()


@router.get("/{conversation_id}/messages", response_model=list[ConversationMessage])
def get_conversation_messages(
    conversation_id: int,
    db: Session = Depends(get_db),
) -> list[ConversationMessage]:
    return DashboardQueryService(db).get_messages(conversation_id)


@router.post(
    "/cleanup-expired",
    response_model=CleanupResponse,
    dependencies=[Depends(require_roles("admin"))],
)
def cleanup_expired_conversations(db: Session = Depends(get_db)) -> dict:
    return {"success": True, **DashboardConversationService(db).cleanup()}


@router.post("/{conversation_id}/take", response_model=ActionResponse)
def take_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
) -> dict:
    return DashboardConversationService(db).take(conversation_id)


@router.post("/{conversation_id}/reply", response_model=ActionResponse)
async def reply_conversation(
    conversation_id: int,
    message: str = Form(...),
    db: Session = Depends(get_db),
) -> dict:
    result = DashboardConversationService(db).reply(conversation_id, message)
    if result.get("success"):
        await manager.broadcast(
            {
                "type": "AGENT_REPLY",
                "conversation_id": conversation_id,
                "message": message,
            }
        )
    return result


@router.post("/{conversation_id}/close", response_model=ActionResponse)
async def close_conversation(
    conversation_id: int,
    resolution: str = Form(default="RESOLVED"),
    note: str = Form(default=""),
    db: Session = Depends(get_db),
) -> dict:
    result = DashboardConversationService(db).close(conversation_id, resolution, note)
    if result.get("success"):
        await manager.broadcast(
            {
                "type": "CONVERSATION_CLOSED",
                "conversation_id": conversation_id,
                "status": result.get("status"),
                "state": result.get("state"),
                "resolution": result.get("resolution"),
            }
        )
    return result
