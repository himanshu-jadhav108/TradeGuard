from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.api.router import api_router
from app.core.config import settings
from app.db.store import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize SQLite schema and baseline records
    init_db()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    description="TradeGuard — Natural language pre-trade safety layer with deterministic risk engine and True Markets integration.",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG or settings.APP_ENV != "production" else None,
    redoc_url="/redoc" if settings.DEBUG or settings.APP_ENV != "production" else None,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(
        status_code=422,
        content={"detail": str(exc)},
    )


@app.get("/")
def root():
    return {
        "service": "TradeGuard Backend",
        "tagline": "Think before you trade. Structured intent. Deterministic validation. User decides.",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/health",
        "mode": settings.TM_ENV,
    }
