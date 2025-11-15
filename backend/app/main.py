"""FastAPI application entry point for Selflytics."""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, Request, status
from fastapi.exceptions import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi_csrf_protect.exceptions import CsrfProtectError
from fastapi_csrf_protect.flexible import CsrfProtect
from pydantic import BaseModel

from app.auth.jwt import verify_token
from app.config import get_settings
from app.dependencies import templates
from app.middleware.telemetry import TelemetryMiddleware
from app.routes import auth, chat, dashboard, garmin
from app.telemetry_config import setup_telemetry, teardown_telemetry
from app.utils.redact import redact_for_logging
from app.utils.request_helpers import is_browser_request


# Load .env file at module import time (before FastAPI app initialization)
# This ensures environment variables are available for all services
BACKEND_DIR = Path(__file__).parent.parent
ENV_FILE = BACKEND_DIR / ".env"
if ENV_FILE.exists():
    load_dotenv(ENV_FILE)


# CSRF Settings
class CsrfSettings(BaseModel):
    """CSRF protection settings.

    Uses fastapi_csrf_protect.flexible.CsrfProtect to support both:
    - HTML forms submitting tokens in request body (POST forms)
    - API/HTMX requests submitting tokens in X-CSRF-Token header (DELETE, etc.)

    Priority: Header is checked first, then body. This allows DELETE requests
    (which cannot have a body) to use headers while POST forms use body.
    """

    secret_key: str
    token_key: str = "fastapi-csrf-token"  # noqa: S105  # Form field name for token, not a password
    # NOTE: cookie_name is ignored by library - it hardcodes "fastapi-csrf-token"
    cookie_samesite: str = "strict"  # Stricter than auth cookie
    cookie_secure: bool = True  # HTTPS only in production
    cookie_httponly: bool = False  # Must be readable by JavaScript (for HTMX)
    cookie_domain: str | None = None
    header_name: str = "X-CSRF-Token"
    max_age: int = 3600  # 1 hour


# Load CSRF configuration
@CsrfProtect.load_config  # type: ignore[arg-type]
def get_csrf_config() -> CsrfSettings:
    """Load CSRF configuration from settings."""
    settings = get_settings()
    return CsrfSettings(
        secret_key=settings.csrf_secret,
        cookie_secure=settings.environment not in ("dev", "development"),
    )


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


# Exception handler for HTTP errors
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> Any:
    """Handle HTTP exceptions.

    For browser/HTMX requests:
    - 401: Redirect to login
    - 403/404/500: Show friendly error template
    For API requests (JSON Accept header), return JSON error response.
    """
    if is_browser_request(request):
        # 401: Redirect to login
        if exc.status_code == status.HTTP_401_UNAUTHORIZED:
            return RedirectResponse(url="/login", status_code=303)

        # 403: Show forbidden error template
        if exc.status_code == status.HTTP_403_FORBIDDEN:
            return templates.TemplateResponse(
                request=request, name="error/403.html", status_code=403
            )

        # 404: Show not found error template
        if exc.status_code == status.HTTP_404_NOT_FOUND:
            return templates.TemplateResponse(
                request=request, name="error/404.html", status_code=404
            )

        # 500+: Show server error template
        if exc.status_code >= 500:
            return templates.TemplateResponse(
                request=request, name="error/500.html", status_code=exc.status_code
            )

    # For API requests or other status codes, return JSON error response
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=exc.headers,
    )


@app.exception_handler(CsrfProtectError)
async def csrf_protect_exception_handler(
    request: Request, _exc: CsrfProtectError
) -> JSONResponse | Any:
    """Handle CSRF validation failures.

    For browser/HTMX requests, return HTML error fragment or page.
    For API requests, return JSON error response.
    """
    # Log CSRF validation failure for security monitoring
    logger.warning(
        "CSRF validation failed: path=%s, method=%s, client=%s",
        request.url.path,
        request.method,
        redact_for_logging(request.client.host if request.client else "unknown"),
    )

    if is_browser_request(request):
        # For HTMX requests, return error fragment
        hx_request = request.headers.get("HX-Request", "") == "true"
        if hx_request:
            return templates.TemplateResponse(
                request=request,
                name="fragments/csrf_error.html",
                status_code=403,
            )
        # For full page requests, show error page
        return templates.TemplateResponse(
            request=request,
            name="error/403.html",
            context={"detail": "CSRF validation failed. Please refresh and try again."},
            status_code=403,
        )

    # For API requests, return JSON
    return JSONResponse(
        status_code=403,
        content={"detail": "CSRF validation failed"},
    )


@app.get("/")
async def root(request: Request) -> RedirectResponse:
    """Root endpoint - redirect based on authentication status.

    - Authenticated users → /chat
    - Unauthenticated users → /login
    """
    # Fast path: Check if token exists before attempting verification
    # This prevents DoS attacks from overwhelming server with JWT verification
    token = request.cookies.get("access_token")

    if not token:
        # No token - redirect to login immediately without expensive verification
        return RedirectResponse(url="/login", status_code=303)

    # Remove "Bearer " prefix if present
    token = token.replace("Bearer ", "") if token.startswith("Bearer ") else token

    try:
        # Validate token
        verify_token(token)
        # Token is valid - redirect to chat (chat-first navigation)
        return RedirectResponse(url="/chat", status_code=303)
    except ValueError:
        # Invalid token - clear it and redirect to login
        response = RedirectResponse(url="/login", status_code=303)
        response.delete_cookie(key="access_token")
        return response


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint.

    Returns:
        Health status and service name
    """
    return {"status": "healthy", "service": "selflytics"}


# Catch-all route for 404 errors (must be last)
# This handles routes not matched by any other endpoint
@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def catch_all(request: Request, path: str) -> Any:  # noqa: ARG001
    """Catch-all handler for 404 errors.

    For browser requests, shows friendly HTML 404 template.
    For API requests, returns JSON error.

    Args:
        request: FastAPI request object
        path: Captured path (unused but required by route pattern)
    """
    if is_browser_request(request):
        return templates.TemplateResponse(request=request, name="error/404.html", status_code=404)

    # API request - return JSON
    return JSONResponse(status_code=404, content={"detail": "Not Found"})
