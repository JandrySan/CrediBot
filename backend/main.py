from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database.init_db import init_db
from app.api.whatsapp import router as whatsapp_router
from app.api.dashboard import router as dashboard_router

from app.api.websocket import router as websocket_router

app = FastAPI(
    title="CrediBot API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    init_db()


app.include_router(whatsapp_router)
app.include_router(dashboard_router)
app.include_router(websocket_router)


@app.get("/")
def root():
    return {
        "message": "CrediBot API funcionando correctamente"
    }


@app.get("/health")
def health_check():
    return {
        "status": "ok"
    }