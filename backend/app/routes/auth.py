"""Authentication routes for user registration and login."""

from fastapi import APIRouter, Depends, Form, HTTPException, Request, Response, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.templating import Jinja2Templates

from app.auth.dependencies import get_current_user, get_user_service
from app.auth.jwt import create_access_token
from app.auth.password import verify_password
from app.config import get_settings
from app.dependencies import get_templates
from app.models.user import UserCreate, UserResponse
from app.services.user_service import UserService


router = APIRouter(tags=["authentication"])


# ========================================
# Template Routes (HTML pages)
# ========================================


@router.get("/register", response_class=HTMLResponse)
async def register_form(
    request: Request, templates: Jinja2Templates = Depends(get_templates)
) -> Response:
    """Display registration form."""
    return templates.TemplateResponse(request=request, name="register.html")


@router.get("/login", response_class=HTMLResponse)
async def login_form(
    request: Request, templates: Jinja2Templates = Depends(get_templates)
) -> Response:
    """Display login form."""
    return templates.TemplateResponse(request=request, name="login.html")


# ========================================
# API Routes (JSON endpoints)
# ========================================


@router.post("/auth/register", response_model=None)
async def register(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    display_name: str = Form(...),
    confirm_password: str = Form(None),
    user_service: UserService = Depends(get_user_service),
    templates: Jinja2Templates = Depends(get_templates),
) -> Response | JSONResponse:
    """Register a new user.

    Args:
        request: FastAPI request object
        email: User email
        password: User password
        display_name: User display name
        confirm_password: Password confirmation (optional, for validation)
        user_service: User service dependency
        templates: Jinja2 templates dependency

    Returns:
        For HTMX requests: Redirect to /dashboard (HX-Redirect header)
        For API requests: UserResponse JSON with created user data

    Raises:
        HTTPException 400: If email already registered or passwords don't match
    """

    # Validate password confirmation if provided
    if confirm_password and password != confirm_password:
        if request.headers.get("HX-Request"):
            # Return form fragment only (not full page) to avoid nesting with hx-swap="outerHTML"
            return templates.TemplateResponse(
                request=request,
                name="fragments/register_form.html",
                context={
                    "errors": {"password": "Passwords do not match"},
                    "email": email,
                    "display_name": display_name,
                },
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match",
        )

    # Create UserCreate model from form data
    user_data = UserCreate(
        email=email,
        password=password,
        display_name=display_name,
    )

    # Check if email already exists
    existing_user = await user_service.get_user_by_email(user_data.email)
    if existing_user:
        # Use generic error to prevent user enumeration (privacy/GDPR compliance)
        # Same pattern as login endpoint - don't reveal if email exists
        generic_error = "Unable to create account. Please try a different email or contact support."

        # For HTMX requests, return form fragment only (not full page)
        if request.headers.get("HX-Request"):
            return templates.TemplateResponse(
                request=request,
                name="fragments/register_form.html",
                context={
                    "errors": {"general": generic_error},
                    "email": user_data.email,
                    "display_name": user_data.display_name,
                },
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        # For API requests, raise HTTPException
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=generic_error,
        )

    # Create new user
    user = await user_service.create_user(user_data)

    # For HTMX requests, redirect to dashboard with auth cookie
    if request.headers.get("HX-Request"):
        # Create JWT access token
        access_token = create_access_token(data={"sub": user.user_id, "email": user.email})

        settings = get_settings()
        response = Response(status_code=status.HTTP_200_OK)
        response.headers["HX-Redirect"] = "/dashboard"
        # Set JWT token in httponly cookie for browser-based auth
        response.set_cookie(
            key="access_token",
            value=f"Bearer {access_token}",
            httponly=True,
            secure=settings.environment != "development",  # Only over HTTPS in production
            samesite="lax",
            max_age=1800,  # 30 minutes (matches JWT expiry)
        )
        return response

    # For API requests, return UserResponse JSON with 201 Created status
    user_response = UserResponse(
        user_id=user.user_id,
        email=user.email,
        profile=user.profile,
        garmin_linked=user.garmin_linked,
    )
    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content=user_response.model_dump(),
    )


@router.post("/auth/login", response_model=None)
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    user_service: UserService = Depends(get_user_service),
    templates: Jinja2Templates = Depends(get_templates),
) -> Response | JSONResponse:
    """Login user and return JWT access token.

    Args:
        request: FastAPI request object
        form_data: OAuth2 form with username (email) and password
        user_service: User service dependency
        templates: Jinja2 templates dependency

    Returns:
        For HTMX requests: Redirect to /dashboard (HX-Redirect header) with Set-Cookie
        For API requests: JSON with access token and token type

    Raises:
        HTTPException 401: If credentials are invalid
    """

    # Get user by email (OAuth2 uses 'username' field for email)
    user = await user_service.get_user_by_email(form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        # For HTMX requests, return form fragment only (not full page)
        if request.headers.get("HX-Request"):
            return templates.TemplateResponse(
                request=request,
                name="fragments/login_form.html",
                context={
                    "errors": {"general": "Incorrect email or password"},
                    "email": form_data.username,
                },
                status_code=status.HTTP_401_UNAUTHORIZED,
            )

        # For API requests, raise HTTPException
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create JWT access token
    access_token = create_access_token(data={"sub": user.user_id, "email": user.email})

    # For HTMX requests, redirect to dashboard with cookie
    if request.headers.get("HX-Request"):
        settings = get_settings()
        response = Response(status_code=status.HTTP_200_OK)
        response.headers["HX-Redirect"] = "/dashboard"
        # Set JWT token in httponly cookie for browser-based auth
        response.set_cookie(
            key="access_token",
            value=f"Bearer {access_token}",
            httponly=True,
            secure=settings.environment != "development",  # Only over HTTPS in production
            samesite="lax",
            max_age=1800,  # 30 minutes (matches JWT expiry)
        )
        return response

    # For API requests, return JSON
    return JSONResponse(content={"access_token": access_token, "token_type": "bearer"})


@router.post("/logout")
async def logout() -> Response:
    """Logout user by clearing authentication cookie.

    Returns:
        Redirect to login page with cleared cookie
    """
    response = Response(status_code=status.HTTP_303_SEE_OTHER)
    response.headers["Location"] = "/login"

    # Clear the access_token cookie
    response.delete_cookie(key="access_token")

    return response


@router.get("/auth/me", response_model=UserResponse)
async def get_me(current_user: UserResponse = Depends(get_current_user)) -> UserResponse:
    """Get current user information.

    Args:
        current_user: Current authenticated user (from token)

    Returns:
        UserResponse with current user data
    """
    return current_user
