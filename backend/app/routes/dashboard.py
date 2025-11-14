"""Dashboard routes."""

from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.auth.dependencies import get_current_user
from app.dependencies import get_templates
from app.models.user import UserResponse


router = APIRouter()


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    user: UserResponse = Depends(get_current_user),
    templates: Jinja2Templates = Depends(get_templates),
) -> Response:
    """Display dashboard with welcome message and feature cards.

    Requires authentication via get_current_user dependency.
    """
    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={"user": user},
    )
