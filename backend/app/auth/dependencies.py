"""Authentication dependencies for FastAPI routes."""

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from typing import Optional

from app.auth.jwt import verify_token
from app.models.user import UserResponse
from app.services.user_service import UserService


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login", auto_error=False)


def get_user_service() -> UserService:
    """Get UserService instance.

    This dependency function allows for easy mocking in tests
    via app.dependency_overrides.

    Returns:
        UserService instance
    """
    return UserService()


async def get_current_user(
    request: Request,
    token: Optional[str] = Depends(oauth2_scheme),
    user_service: UserService = Depends(get_user_service),  # noqa: B008
) -> UserResponse:
    """Get current authenticated user from JWT token.

    Checks for JWT token in:
    1. Authorization header (for API requests)
    2. access_token cookie (for browser/HTMX requests)

    Args:
        request: FastAPI request object
        token: JWT access token from Authorization header (optional)
        user_service: User service dependency

    Returns:
        UserResponse with current user data

    Raises:
        HTTPException 401: If token is invalid or user not found
    """
    # Try Authorization header first
    if not token:
        # Fall back to cookie
        cookie_token = request.cookies.get("access_token")
        if cookie_token:
            # Remove "Bearer " prefix if present
            token = cookie_token.replace("Bearer ", "") if cookie_token.startswith("Bearer ") else cookie_token

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        token_data = verify_token(token)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None

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
