"""FastAPI application entry point with CORS, error handling, and route registration."""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.utils.rate_limiter import limiter

from app.config import settings
from app.database import engine, Base

# Import all models so SQLAlchemy creates the tables
from app.models.user import User        # noqa: F401
from app.models.document import Document  # noqa: F401
from app.models.query import QueryRecord  # noqa: F401
from app.models.audit import AuditLog    # noqa: F401

# Create all tables
Base.metadata.create_all(bind=engine)

# ── Rate limiter ────────────────────────────────────────────────────
# Limiter instantiated in app.utils.rate_limiter

# ── FastAPI app ─────────────────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ── CORS ────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

app.include_router(auth_router)
app.include_router(documents_router)
app.include_router(queries_router)
app.include_router(admin_router)


# ── Health check ────────────────────────────────────────────────────
@app.get("/api/v1/health")
def health_check():
    try:
        from app.services import vector_store
        vec_stats = vector_store.get_collection_stats()
        chunks = vec_stats.get("total_chunks", 0)
    except Exception as e:
        print(f"Health check vector store error: {e}")
        chunks = 0
        
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "vector_chunks": chunks,
    }
