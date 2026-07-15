"""Compatibilidad temporal para imports existentes.

El procesamiento de mensajes vive exclusivamente en ``ConversationOrchestrator``.
"""

from app.services.conversation.session_service import ConversationSessionService

ConversationManager = ConversationSessionService
