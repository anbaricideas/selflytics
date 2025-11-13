"""Garmin integration routes."""

import logging

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from telemetry.logging_utils import redact_for_logging

from app.auth.dependencies import get_current_user
from app.dependencies import get_templates
from app.models.user import UserResponse
from app.services.garmin_service import GarminService


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/garmin", tags=["garmin"])


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


@router.post("/link", response_class=HTMLResponse)
async def link_garmin_account(
    username: str = Form(...),
    password: str = Form(...),
    current_user: UserResponse = Depends(get_current_user),
):
    """Link Garmin account to user.

    Returns HTML fragment for HTMX swap (outerHTML).
    Accepts form data from HTMX form submission.
    """
    service = GarminService(current_user.user_id)

    success = await service.link_account(
        username=username,
        password=password,
    )

    if not success:
        # Return error HTML fragment for HTMX
        return HTMLResponse(
            content="""
            <div class="bg-red-50 border border-red-200 rounded-lg p-6" data-testid="error-message">
                <p class="text-red-800 font-semibold">Failed to link Garmin account</p>
                <p class="text-sm text-red-600 mt-2">Please check your credentials and try again.</p>
            </div>
            """,
            status_code=400,
        )

    # Return success HTML fragment for HTMX swap
    # This replaces the form with the "linked" status view
    return HTMLResponse(
        content="""
        <div class="bg-green-50 border border-green-200 rounded-lg p-6" data-testid="garmin-status-linked">
            <div class="flex items-start">
                <div class="flex-shrink-0">
                    <svg class="h-6 w-6 text-green-500" fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
                    </svg>
                </div>
                <div class="ml-3 flex-1">
                    <p class="text-green-800 font-semibold">Garmin account linked</p>
                    <p class="text-sm text-gray-600 mt-2">Your Garmin data is being synchronized automatically.</p>

                    <button
                        data-testid="button-sync-garmin"
                        hx-post="/garmin/sync"
                        hx-swap="outerHTML"
                        hx-indicator="#sync-spinner"
                        class="mt-4 inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors"
                    >
                        <span id="sync-spinner" class="htmx-indicator">
                            <svg class="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                            </svg>
                        </span>
                        Sync Now
                    </button>
                </div>
            </div>
        </div>
        """,
        status_code=200,
    )


@router.post("/sync", response_class=HTMLResponse)
async def sync_garmin_data(
    current_user: UserResponse = Depends(get_current_user),
):
    """Manually trigger Garmin data sync.

    Returns HTML fragment for HTMX swap (outerHTML).
    """
    service = GarminService(current_user.user_id)

    try:
        await service.sync_recent_data()
        # Return success HTML fragment
        return HTMLResponse(
            content="""
            <div class="bg-green-50 border border-green-200 rounded-lg p-4" data-testid="sync-success">
                <p class="text-green-800 font-semibold">Sync completed successfully</p>
                <p class="text-sm text-green-600 mt-1">Your latest Garmin data has been synchronized.</p>
            </div>
            """,
            status_code=200,
        )
    except Exception as e:
        logger.error(
            "Sync failed for user %s: %s", current_user.user_id, redact_for_logging(str(e))
        )
        # Return error HTML fragment
        return HTMLResponse(
            content="""
            <div class="bg-red-50 border border-red-200 rounded-lg p-4" data-testid="sync-error">
                <p class="text-red-800 font-semibold">Sync failed</p>
                <p class="text-sm text-red-600 mt-1">Please try again later.</p>
            </div>
            """,
            status_code=500,
        )


@router.delete("/link")
async def unlink_garmin_account(
    current_user: UserResponse = Depends(get_current_user),
):
    """Unlink Garmin account by deleting tokens and cache."""
    service = GarminService(current_user.user_id)

    try:
        # Delete tokens and invalidate cache
        await service.unlink_account()
        return {"message": "Garmin account unlinked successfully"}
    except Exception as e:
        logger.error(
            "Failed to unlink for user %s: %s", current_user.user_id, redact_for_logging(str(e))
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to unlink Garmin account",
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
