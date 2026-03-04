"""FastAPI application entry point with security hardening, CORS, and route registration."""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from starlette.middleware.base import BaseHTTPMiddleware

from app.utils.rate_limiter import limiter

from app.config import settings
from app.database import engine, Base

# Import all models so SQLAlchemy creates the tables
from app.models.user import User        # noqa: F401
from app.models.document import Document  # noqa: F401
from app.models.query import QueryRecord  # noqa: F401
from app.models.audit import AuditLog    # noqa: F401
from app.models.document_version import DocumentVersion  # noqa: F401
from app.models.conversation import Conversation, ConversationMessage  # noqa: F401

# Create all tables
Base.metadata.create_all(bind=engine)


# ── Security Headers Middleware ────────────────────────────────────
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Cache-Control"] = "no-store"
        if settings.FORCE_HTTPS:
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )
        return response


# ── HTTPS Redirect Middleware ──────────────────────────────────────
class HTTPSRedirectMiddleware(BaseHTTPMiddleware):
    """Redirect HTTP to HTTPS in production."""
    async def dispatch(self, request: Request, call_next):
        if settings.FORCE_HTTPS:
            forwarded_proto = request.headers.get("x-forwarded-proto", "")
            if forwarded_proto == "http":
                url = request.url.replace(scheme="https")
                return JSONResponse(
                    status_code=301,
                    headers={"Location": str(url)},
                    content={"detail": "Redirecting to HTTPS"},
                )
        return await call_next(request)


# ── FastAPI app ─────────────────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    description="FAR Compliance Copilot: AI-powered federal procurement compliance platform",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ── Middleware Stack (order matters: last added = first executed) ──
# GZip compression for responses
app.add_middleware(GZipMiddleware, minimum_size=1000)

# CORS - configurable from environment
origins = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-API-Key", "X-Request-ID"],
)

# Security headers
app.add_middleware(SecurityHeadersMiddleware)

# HTTPS redirect
app.add_middleware(HTTPSRedirectMiddleware)


# ── Global error handler ───────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if settings.DEBUG else "Something went wrong. Our team has been notified.",
        },
    )

# ── Register routers ───────────────────────────────────────────────
from app.routes.auth import router as auth_router
from app.routes.documents import router as documents_router
from app.routes.queries import router as queries_router
from app.routes.admin import router as admin_router
from app.routes.compliance import router as compliance_router

app.include_router(auth_router)
app.include_router(documents_router)
app.include_router(queries_router)
app.include_router(admin_router)
app.include_router(compliance_router)


# ── Health check ────────────────────────────────────────────────────
@app.get("/api/v1/health")
def health_check():
    try:
        from app.services import vector_store
        vec_stats = vector_store.get_collection_stats()
        chunks = vec_stats.get("total_chunks", 0)
    except Exception as e:
        if settings.DEBUG:
            print(f"Health check vector store error: {e}")
        chunks = 0

    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "vector_chunks": chunks,
        "debug_mode": settings.DEBUG,
    }
