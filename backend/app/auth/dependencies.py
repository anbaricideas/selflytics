"""Authentication dependencies for FastAPI routes."""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.auth.jwt import verify_token
from app.models.user import UserResponse
from app.services.user_service import UserService


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


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
