import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import enroll, verify
from api.core.storage import init_db
from api.security import RateLimitMiddleware, RequestBodyLimitMiddleware

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("keycadence")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler.

    Runs once at startup to initialize the database schema (creates the
    baselines table if it does not exist). The yield point is where the
    application is live and serving requests.
    """
    logger.info("Initializing database")
    init_db()
    logger.info("Database ready")
    yield
    logger.info("Shutting down")


app = FastAPI(
    title="KeyCadence",
    description="Behavioral biometric authentication API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(RequestBodyLimitMiddleware, max_bytes=1_048_576)
app.add_middleware(RateLimitMiddleware, max_requests=60, window_seconds=60)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[],
    allow_credentials=False,
    allow_methods=["POST", "GET", "DELETE"],
    allow_headers=["X-API-Key", "Content-Type"],
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
