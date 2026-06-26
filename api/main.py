from contextlib import asynccontextmanager

from fastapi import FastAPI

from api.routes import enroll, verify
from api.core.storage import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="KeyCadence",
    description="Behavioral biometric authentication API",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(enroll.router)
app.include_router(verify.router)


@app.get("/")
async def root():
    return {"message": "KeyCadence API", "docs": "/docs"}


@app.get("/health")
async def health():
    return {"status": "healthy"}
