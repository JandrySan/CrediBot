from fastapi import FastAPI

from app.database.init_db import init_db

app = FastAPI(
    title="CrediBot API",
    version="1.0.0"
)


@app.on_event("startup")
def startup():
    init_db()


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