"""FastAPI application entry point for Selflytics."""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from app.config import get_settings
from app.middleware.telemetry import TelemetryMiddleware
from app.routes import auth, chat, dashboard, garmin
from app.telemetry_config import setup_telemetry, teardown_telemetry


# Load .env file at module import time (before FastAPI app initialization)
# This ensures environment variables are available for all services
BACKEND_DIR = Path(__file__).parent.parent
ENV_FILE = BACKEND_DIR / ".env"
if ENV_FILE.exists():
    load_dotenv(ENV_FILE)


logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager.

    Handles startup and shutdown tasks including telemetry configuration.
    """
    # Startup
    settings = get_settings()

    # Validate production configuration
    if settings.jwt_secret == "dev-secret-change-in-production":  # noqa: S105  # nosec B105
        if settings.environment.startswith("preview-"):
            logger.warning(
                "Preview environment '%s' using default JWT_SECRET. "
                "This is acceptable for ephemeral preview deployments.",
                settings.environment,
            )
        elif settings.environment not in ("dev", "development"):
            logger.critical(
                "SECURITY WARNING: Using default JWT_SECRET in production environment! "
                "Set JWT_SECRET environment variable immediately."
            )
            raise ValueError(
                "Default JWT_SECRET is not allowed in production. Set JWT_SECRET environment variable."
            )

    telemetry_context = setup_telemetry()
    app.state.telemetry_context = telemetry_context

    yield

    # Shutdown
    teardown_telemetry(telemetry_context)


settings = get_settings()

# Create FastAPI app with lifespan
app = FastAPI(
    title="Selflytics API",
    description="AI-powered analysis for quantified self data",
    version="0.1.0",
    debug=settings.debug,
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add telemetry middleware
app.add_middleware(
    TelemetryMiddleware,
    skip_paths={
        "/health",  # Health checks
        "/openapi.json",  # OpenAPI schema
    },
)

# Include routers
app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(dashboard.router)
app.include_router(garmin.router)


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
