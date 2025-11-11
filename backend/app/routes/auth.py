"""Authentication routes for user registration and login."""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from app.auth.jwt import create_access_token, verify_token
from app.auth.password import verify_password
from app.models.user import UserCreate, UserResponse
from app.services.user_service import UserService


router = APIRouter(prefix="/auth", tags=["authentication"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate):
    """Register a new user.

    Args:
        user_data: User registration data (email, password, display_name)

    Returns:
        UserResponse with created user data (no password)

    Raises:
        HTTPException 400: If email already registered
    """
    user_service = UserService()

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


@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Login user and return JWT access token.

    Args:
        form_data: OAuth2 form with username (email) and password

    Returns:
        Access token and token type

    Raises:
        HTTPException 401: If credentials are invalid
    """
    user_service = UserService()

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


async def get_current_user(token: str = Depends(oauth2_scheme)) -> UserResponse:
    """Get current authenticated user from JWT token.

    Args:
        token: JWT access token from Authorization header

    Returns:
        UserResponse with current user data

    Raises:
        HTTPException 401: If token is invalid or user not found
    """
    try:
        token_data = verify_token(token)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None

    user_service = UserService()
    user = await user_service.get_user_by_id(token_data.user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return UserResponse(
        user_id=user.user_id,
        email=user.email,
        profile=user.profile,
        garmin_linked=user.garmin_linked,
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: UserResponse = Depends(get_current_user)):
    """Get current user information.

    Args:
        current_user: Current authenticated user (from token)

    Returns:
        UserResponse with current user data
    """
    return current_user
