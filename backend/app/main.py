"""FastAPI application entry point for Selflytics."""

from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from app.config import settings
from app.routes import auth, dashboard


# Load .env file at module import time
BACKEND_DIR = Path(__file__).parent.parent
ENV_FILE = BACKEND_DIR / ".env"
if ENV_FILE.exists():
    load_dotenv(ENV_FILE)


app = FastAPI(
    title="Selflytics API",
    description="AI-powered analysis for quantified self data",
    version="0.1.0",
    debug=settings.debug,
)

# CORS middleware (development only)
if settings.debug:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Include routers
app.include_router(auth.router)
app.include_router(dashboard.router)


@app.get("/")
async def root() -> RedirectResponse:
    """Root endpoint - redirect to login page.

    In Phase 2, we'll check auth status and redirect accordingly:
    - Authenticated users → /dashboard
    - Unauthenticated users → /login
    """
    return RedirectResponse(url="/login", status_code=303)


@app.get("/health")
async def health_check():
    """Health check endpoint.

    Returns:
        Health status and service name
    """
    return {"status": "healthy", "service": "selflytics"}
