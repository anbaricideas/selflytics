"""Garmin integration routes."""

import logging

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from fastapi_csrf_protect import CsrfProtect
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
    csrf_protect: CsrfProtect = Depends(),
    templates=Depends(get_templates),
):
    """Display Garmin account linking form with CSRF token."""
    csrf_token, signed_token = csrf_protect.generate_csrf_tokens()
    response = templates.TemplateResponse(
        request=request,
        name="settings_garmin.html",
        context={
            "user": current_user,
            "csrf_token": csrf_token,
        },
    )
    csrf_protect.set_csrf_cookie(signed_token, response)
    return response


@router.post("/link", response_class=HTMLResponse)
async def link_garmin_account(
    request: Request,
    csrf_protect: CsrfProtect = Depends(),
    username: str = Form(...),
    password: str = Form(...),
    current_user: UserResponse = Depends(get_current_user),
    templates=Depends(get_templates),
):
    """Link Garmin account to user.

    Returns HTML fragment for HTMX swap (outerHTML).
    Accepts form data from HTMX form submission.
    """
    # Validate CSRF token FIRST
    await csrf_protect.validate_csrf(request)

    try:
        service = GarminService(current_user.user_id)

        success = await service.link_account(
            username=username,
            password=password,
        )

        if not success:
            # Generate NEW token for form re-render
            csrf_token, signed_token = csrf_protect.generate_csrf_tokens()
            response = templates.TemplateResponse(
                request=request,
                name="fragments/garmin_link_form.html",
                context={
                    "csrf_token": csrf_token,
                    "error_message": "Please check your credentials and try again.",
                },
                status_code=400,
            )
            csrf_protect.set_csrf_cookie(signed_token, response)
            return response

        # Return success HTML fragment for HTMX swap
        # This replaces the form with the "linked" status view
        return templates.TemplateResponse(
            request=request,
            name="fragments/garmin_linked_success.html",
            status_code=200,
        )
    except HTTPException:
        raise  # Re-raise expected HTTP exceptions
    except Exception as e:
        # Log detailed error (with redaction) for debugging
        logger.error(
            "Garmin link failed for user %s: %s",
            current_user.user_id,
            redact_for_logging(str(e)),
        )

        # Generate NEW token for form re-render
        csrf_token, signed_token = csrf_protect.generate_csrf_tokens()
        response = templates.TemplateResponse(
            request=request,
            name="fragments/garmin_link_form.html",
            context={
                "csrf_token": csrf_token,
                "error_title": "Something went wrong",
                "error_message": "An unexpected error occurred. Please try again later.",
            },
            status_code=500,
        )
        csrf_protect.set_csrf_cookie(signed_token, response)
        return response


@router.post("/sync", response_class=HTMLResponse)
async def sync_garmin_data(
    request: Request,
    csrf_protect: CsrfProtect = Depends(),
    current_user: UserResponse = Depends(get_current_user),
    templates=Depends(get_templates),
):
    """Manually trigger Garmin data sync.

    Returns HTML fragment for HTMX swap (outerHTML).
    """
    # Validate CSRF token FIRST
    await csrf_protect.validate_csrf(request)

    service = GarminService(current_user.user_id)

    try:
        await service.sync_recent_data()
        # Return success HTML fragment
        return templates.TemplateResponse(
            request=request,
            name="fragments/garmin_sync_success.html",
            status_code=200,
        )
    except Exception as e:
        logger.error(
            "Sync failed for user %s: %s", current_user.user_id, redact_for_logging(str(e))
        )
        # Generate NEW token for potential retry
        _csrf_token, signed_token = csrf_protect.generate_csrf_tokens()
        response = templates.TemplateResponse(
            request=request,
            name="fragments/garmin_sync_error.html",
            status_code=500,
        )
        csrf_protect.set_csrf_cookie(signed_token, response)
        return response


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
