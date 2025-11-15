"""Dashboard and settings routes."""

from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.auth.dependencies import get_current_user
from app.dependencies import get_templates
from app.models.user import UserResponse


router = APIRouter()


@router.get("/dashboard")
async def dashboard_redirect() -> RedirectResponse:
    """Redirect old dashboard URL to new settings page.

    Returns 301 (permanent redirect) to signal this is a permanent change.
    This helps with SEO and allows browsers to cache the redirect.
    """
    return RedirectResponse("/settings", status_code=301)


@router.get("/settings", response_class=HTMLResponse)
async def settings_page(
    request: Request,
    user: UserResponse = Depends(get_current_user),
    templates: Jinja2Templates = Depends(get_templates),
) -> Response:
    """Settings hub page with Garmin and profile management links.

    Requires authentication via get_current_user dependency.
    """
    return templates.TemplateResponse(
        request=request,
        name="settings.html",
        context={"user": user},
    )
