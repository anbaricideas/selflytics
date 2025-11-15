"""Dashboard and settings routes."""

from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi_csrf_protect.flexible import CsrfProtect

from app.auth.dependencies import get_current_user
from app.dependencies import get_templates
from app.models.user import UserResponse


router = APIRouter()


@router.get("/")
async def root_redirect(request: Request) -> RedirectResponse:
    """Redirect root URL to chat (authenticated) or login (unauthenticated).

    Checks for authentication by looking for access_token cookie.
    Returns 303 (See Other) as this is a conditional redirect based on state.

    Args:
        request: FastAPI request object

    Returns:
        RedirectResponse to /chat/ (authenticated) or /login (unauthenticated)
    """
    # Check if user has authentication cookie
    has_auth_token = request.cookies.get("access_token") is not None

    if has_auth_token:
        return RedirectResponse("/chat/", status_code=303)
    return RedirectResponse("/login", status_code=303)


@router.get("/dashboard")
async def dashboard_redirect() -> RedirectResponse:
    """Redirect old dashboard URL to new settings page.

    Returns 301 (permanent redirect) to signal this is a permanent change.
    This helps with SEO and allows browsers to cache the redirect.

    Note: No auth required here - authentication is checked at /settings destination.
    This simplifies the redirect logic and avoids duplicate auth checks.
    """
    return RedirectResponse("/settings", status_code=301)


@router.get("/settings", response_class=HTMLResponse)
async def settings_page(
    request: Request,
    user: UserResponse = Depends(get_current_user),
    csrf_protect: CsrfProtect = Depends(),
    templates: Jinja2Templates = Depends(get_templates),
) -> Response:
    """Settings hub page with Garmin and profile management links.

    Requires authentication via get_current_user dependency.
    Generates CSRF token for logout form protection.
    """
    # Generate CSRF token pair for logout form
    csrf_token, signed_token = csrf_protect.generate_csrf_tokens()

    response = templates.TemplateResponse(
        request=request,
        name="settings.html",
        context={"user": user, "csrf_token": csrf_token},
    )

    # Set CSRF cookie
    csrf_protect.set_csrf_cookie(signed_token, response)

    return response
