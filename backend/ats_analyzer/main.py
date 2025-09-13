"""FastAPI main application."""

import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from ats_analyzer.api.routes import router, ats_exception_handler
from ats_analyzer.core.errors import ATSAnalyzerException
from ats_analyzer.core.config import get_settings
from ats_analyzer.core.logging import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager."""
    # Startup
    setup_logging()
    logger = structlog.get_logger()
    logger.info("Starting ATS Analyzer API")
    
    # Load ML models on startup
    try:
        import spacy
        spacy.load("en_core_web_sm")
        logger.info("Loaded spaCy model")
    except OSError:
        logger.warning("spaCy model not found - run: python -m spacy download en_core_web_sm")
    
    try:
        from sentence_transformers import SentenceTransformer
        SentenceTransformer("all-MiniLM-L6-v2")
        logger.info("Loaded sentence transformer model")
    except Exception as e:
        logger.warning("Failed to load sentence transformer", error=str(e))
    
    yield
    
    # Shutdown
    logger.info("Shutting down ATS Analyzer API")


app = FastAPI(
    title="ATS Analyzer API",
    description="Resume analysis and ATS compatibility checker",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_request_id_middleware(request: Request, call_next):
    """Add request ID and timing to all requests."""
    import uuid
    
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    
    start_time = time.time()
    
    # Add request ID to structlog context
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(request_id=request_id)
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time"] = str(process_time)
    
    return response


# Add exception handlers
app.add_exception_handler(ATSAnalyzerException, ats_exception_handler)

# Include API routes
app.include_router(router, prefix="/api/v1")


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy", "service": "ats-analyzer"}


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint."""
    return {"message": "ATS Analyzer API", "docs": "/docs"}
