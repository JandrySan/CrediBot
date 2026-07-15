from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.auth import router as auth_router
from app.api.dashboard import router as dashboard_router
from app.api.websocket import router as websocket_router
from app.api.whatsapp import router as whatsapp_router
from app.config.runtime import validate_runtime_configuration
from app.config.settings import settings
from app.database.migrations import prepare_database
from app.database.session import SessionLocal
from app.services.conversation.session_service import ConversationSessionService


@asynccontextmanager
async def lifespan(_app: FastAPI):
    validate_runtime_configuration(settings)
    prepare_database()
    db = SessionLocal()
    try:
        with db.begin():
            ConversationSessionService(db).cleanup_sessions()
    finally:
        db.close()
    yield


app = FastAPI(
    title="CrediBot API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(whatsapp_router)
app.include_router(dashboard_router)
app.include_router(websocket_router)


@app.get("/")
def root():
    return {"message": "CrediBot API funcionando correctamente"}


@app.get("/health")
def health_check():
    return {"status": "ok"}
