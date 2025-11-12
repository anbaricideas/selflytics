"""Authentication routes for user registration and login."""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from fastapi.security import OAuth2PasswordRequestForm

from app.auth.dependencies import get_current_user, get_user_service
from app.auth.jwt import create_access_token
from app.auth.password import verify_password
from app.dependencies import get_templates
from app.models.user import UserCreate, UserResponse
from app.services.user_service import UserService


router = APIRouter(tags=["authentication"])


# ========================================
# Template Routes (HTML pages)
# ========================================


@router.get("/register", response_class=HTMLResponse)
async def register_form(request: Request, templates=Depends(get_templates)) -> HTMLResponse:
    """Display registration form."""
    return templates.TemplateResponse(request=request, name="register.html")


@router.get("/login", response_class=HTMLResponse)
async def login_form(request: Request, templates=Depends(get_templates)) -> HTMLResponse:
    """Display login form."""
    return templates.TemplateResponse(request=request, name="login.html")


# ========================================
# API Routes (JSON endpoints)
# ========================================


@router.post("/auth/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    user_service: UserService = Depends(get_user_service),
):
    """Register a new user.

    Args:
        user_data: User registration data (email, password, display_name)

    Returns:
        UserResponse with created user data (no password)

    Raises:
        HTTPException 400: If email already registered
    """

    # Check if email already exists
    existing_user = await user_service.get_user_by_email(user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Create new user
    user = await user_service.create_user(user_data)

    return UserResponse(
        user_id=user.user_id,
        email=user.email,
        profile=user.profile,
        garmin_linked=user.garmin_linked,
    )


@router.post("/auth/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    user_service: UserService = Depends(get_user_service),
):
    """Login user and return JWT access token.

    Args:
        form_data: OAuth2 form with username (email) and password

    Returns:
        Access token and token type

    Raises:
        HTTPException 401: If credentials are invalid
    """

    # Get user by email (OAuth2 uses 'username' field for email)
    user = await user_service.get_user_by_email(form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create JWT access token
    access_token = create_access_token(data={"sub": user.user_id, "email": user.email})

    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/auth/me", response_model=UserResponse)
async def get_me(current_user: UserResponse = Depends(get_current_user)):
    """Get current user information.

    Args:
        current_user: Current authenticated user (from token)

    Returns:
        UserResponse with current user data
    """
    return current_user
