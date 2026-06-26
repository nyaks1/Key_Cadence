from contextlib import asynccontextmanager

from fastapi import FastAPI

from api.routes import enroll, verify
from api.core.storage import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler.

    Runs once at startup to initialize the database schema (creates the
    baselines table if it does not exist). The yield point is where the
    application is live and serving requests.
    """
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
    """Root endpoint. Returns API name and a link to the docs."""
    return {"message": "KeyCadence API", "docs": "/docs"}


@app.get("/health")
async def health():
    """Health check endpoint for uptime monitoring and load balancers."""
    return {"status": "healthy"}
