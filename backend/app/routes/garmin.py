"""Garmin integration routes."""

import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from app.auth.dependencies import get_current_user
from app.dependencies import get_templates
from app.models.user import UserResponse
from app.services.garmin_service import GarminService


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/garmin", tags=["garmin"])


class GarminLinkRequest(BaseModel):
    """Request model for linking Garmin account."""

    username: str
    password: str


@router.get("/link", response_class=HTMLResponse)
async def garmin_link_page(
    request: Request,
    current_user: UserResponse = Depends(get_current_user),
    templates=Depends(get_templates),
):
    """Display Garmin account linking form."""
    return templates.TemplateResponse(
        request=request,
        name="settings_garmin.html",
        context={"user": current_user},
    )


@router.post("/link")
async def link_garmin_account(
    link_request: GarminLinkRequest,
    current_user: UserResponse = Depends(get_current_user),
):
    """Link Garmin account to user."""
    service = GarminService(current_user.user_id)

    success = await service.link_account(
        username=link_request.username,
        password=link_request.password,
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to link Garmin account. Check credentials.",
        )

    return {"message": "Garmin account linked successfully"}


@router.post("/sync")
async def sync_garmin_data(
    current_user: UserResponse = Depends(get_current_user),
):
    """Manually trigger Garmin data sync."""
    service = GarminService(current_user.user_id)

    try:
        await service.sync_recent_data()
        return {"message": "Sync completed successfully"}
    except Exception as e:
        logger.error("Sync failed for user %s: %s", current_user.user_id, str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sync failed: {e!s}",
        ) from e


@router.get("/status")
async def garmin_status(
    current_user: UserResponse = Depends(get_current_user),
):
    """Get Garmin account link status."""
    return {
        "linked": current_user.garmin_linked,
        "user_id": current_user.user_id,
    }
