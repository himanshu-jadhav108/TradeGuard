from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.router import api_router
from app.core.config import settings
from app.db.store import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize SQLite schema and seed demo records
    init_db()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    description="TradeGuard — Natural language trade execution layer with deterministic risk engine and True Markets integration.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/")
def root():
    return {
        "service": "TradeGuard Backend",
        "tagline": "Think before you trade.",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/health",
        "mode": settings.TM_ENV,
    }
