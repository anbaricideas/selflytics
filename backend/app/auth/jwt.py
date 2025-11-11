"""JWT token handling for authentication.

This module provides functions for creating and verifying JWT access tokens
used for user authentication. Tokens are signed with HS256 and include
user_id (sub) and email claims.
"""

from datetime import UTC, datetime, timedelta

from jose import JWTError, jwt
from pydantic import BaseModel

from app.config import settings


class TokenData(BaseModel):
    """Data extracted from a verified JWT token."""

    user_id: str
    email: str


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Create a JWT access token.

    Args:
        data: Dictionary containing token claims (must include 'sub' and 'email')
        expires_delta: Optional custom expiration time. Defaults to configured value.

    Returns:
        Encoded JWT token string

    Note:
        The token includes an 'exp' (expiration) claim automatically.
    """
    to_encode = data.copy()

    # Set expiration time
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes)

    to_encode["exp"] = expire

    # Encode and return JWT
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def verify_token(token: str) -> TokenData:
    """Decode and verify a JWT token.

    Args:
        token: The JWT token string to verify

    Returns:
        TokenData containing user_id and email extracted from the token

    Raises:
        ValueError: If the token is invalid, expired, or missing required claims

    Note:
        This function validates the token signature and expiration time.
    """
    try:
        # Decode and verify token
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])

        # Extract required claims
        user_id: str | None = payload.get("sub")
        email: str | None = payload.get("email")

        # Validate required claims are present
        if user_id is None or email is None:
            raise ValueError("Invalid token payload")

        return TokenData(user_id=user_id, email=email)

    except JWTError as e:
        # Catch all JWT errors (expired, invalid signature, malformed, etc.)
        raise ValueError(f"Invalid or expired token: {e}") from e
    except (TypeError, AttributeError) as e:
        # Handle None or invalid input types
        raise ValueError(f"Invalid token format: {e}") from e
