"""
SiagaMap AI Backend — FastAPI Application Entry Point

Platform pemantauan bencana real-time yang mengintegrasikan data BMKG
dengan kecerdasan buatan (Machine Learning) untuk mitigasi bencana.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from backend.routers import disasters, analysis, chat
from backend.models.risk_model import train_model
from backend.models.hoax_model import train_hoax_model
from backend.models.chat_engine import get_chat_engine

# ─── Configuration ───────────────────────────────────────────────

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


# ─── Application Lifespan ───────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown logic."""
    # ── Startup ──
    logger.info("=" * 60)
    logger.info("  SiagaMap AI Backend — Starting Up")
    logger.info("=" * 60)

    # Train the risk classification model
    logger.info("Initializing risk classification model...")
    train_model()
    logger.info("✅ Risk model ready")

    # Train the hoax classification model
    logger.info("Initializing hoax classification model...")
    train_hoax_model()
    logger.info("✅ Hoax model ready")

    # Initialize the chat engine
    logger.info("Initializing chat engine...")
    get_chat_engine()
    logger.info("✅ Chat engine ready")


    logger.info("=" * 60)
    logger.info("  🚀 SiagaMap AI Backend is READY")
    logger.info("  📡 API Docs: http://localhost:8000/docs")
    logger.info("=" * 60)

    yield

    # ── Shutdown ──
    logger.info("SiagaMap AI Backend — Shutting Down")


# ─── FastAPI App ─────────────────────────────────────────────────

app = FastAPI(
    title="SiagaMap AI Backend",
    description=(
        "Backend API untuk platform pemantauan bencana SiagaMap AI. "
        "Mengintegrasikan data BMKG real-time dengan model Machine Learning "
        "untuk analisis risiko dan panduan mitigasi bencana."
    ),
    version="1.0.0",
    lifespan=lifespan,
)


# ─── CORS Middleware ─────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",       # Next.js dev server
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Register Routers ───────────────────────────────────────────

app.include_router(disasters.router)
app.include_router(analysis.router)
app.include_router(chat.router)


# ─── Health Check ────────────────────────────────────────────────

@app.get("/", tags=["health"])
async def root():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "SiagaMap AI Backend",
        "version": "1.0.0",
        "engine": "Python + scikit-learn",
    }


@app.get("/health", tags=["health"])
async def health():
    """Detailed health check."""
    return {
        "status": "healthy",
        "models": {
            "risk_classifier": "RandomForestClassifier (trained)",
            "chat_engine": "TF-IDF + Cosine Similarity (ready)",
        },
        "data_source": "BMKG Open API",
    }


# ─── Run Server ─────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
