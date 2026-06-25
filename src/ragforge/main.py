import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware

from src.ragforge.config import settings
from src.ragforge.core.exceptions import AppError
from src.ragforge.core.logger import setup_logging
from src.ragforge.db.session import init_db
from src.ragforge.routes import index

setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(
    title="RagForge",
    version="1.0.0",
    description=(
        "Production-grade multimodal RAG architecture providing multi-tenant document ingestion, "
        "hierarchical element extraction, cross-modal summarizations, and persistent chat streams."
    ),
)

# ---- Middleware Registration ----
# Order matters: Middlewares execute in reverse registration order for requests, and forward order for responses.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Compress network transport frames exceeding 1KB limits cleanly
app.add_middleware(GZipMiddleware, minimum_size=1000)


@app.middleware("http")
async def skip_gzip_for_sse(request: Request, call_next):
    """Intercept token streaming endpoints to bypass GZip compression buffering limits.

    GZip middleware buffers text fragments before flushing, which stalls token-by-token streaming.
    Stripping the Accept-Encoding header for SSE avenues ensures instant packet delivery.
    """
    if request.url.path.endswith("/ask"):
        scope = request.scope
        headers = [(k, v) for k, v in scope["headers"] if k != b"accept-encoding"]
        scope["headers"] = headers
    response = await call_next(request)
    return response


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - start) * 1000
    logger.info(
        "%s %s -> Status: %d | Latency: %.1f ms",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    return response


# ---- Core Exception Handlers ----
@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


# ---- Route Aggregation Mount ----
app.include_router(index.router)


# ---- Lifecycle Callbacks ----
@app.on_event("startup")
async def on_startup():
    if settings.SECRET_KEY == "change-this-to-a-long-random-secret-in-production":
        if not settings.DEBUG:
            raise RuntimeError(
                "SECRET_KEY is the insecure default. "
                "Set a strong random secret in .env before running in production."
            )
        logger.warning("Using default SECRET_KEY - do not use in production!")

    init_db()


@app.get("/", summary="API Root Verification Entry Point")
async def root():
    return {
        "status": "online",
        "application": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "message": "RagForge Multimodal Pipeline Gateway Active",
    }
