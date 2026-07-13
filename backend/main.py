import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes import auth_router, repositories_router, reviews_router, search_router
from backend.config import get_settings

settings = get_settings()

logging.basicConfig(
    level=logging.DEBUG if settings.app_debug else logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)

app = FastAPI(
    title="AI Code Review & Repository Intelligence Platform",
    description="Semantic search and AI-powered code review for Git repositories.",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ──────────────────────────────────────────────────────────────────
API_PREFIX = "/api/v1"

app.include_router(auth_router, prefix=API_PREFIX)
app.include_router(repositories_router, prefix=API_PREFIX)
app.include_router(search_router, prefix=API_PREFIX)
app.include_router(reviews_router, prefix=API_PREFIX)


@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "ok", "version": "0.1.0"}
