"""Password hashing utilities using bcrypt.

This module provides secure password hashing and verification using the
bcrypt algorithm. Bcrypt is designed to be computationally expensive to
prevent brute-force attacks.

Security notes:
- Bcrypt automatically generates a unique salt for each password
- Bcrypt has a 72-byte limit - passwords are truncated automatically
- Hash verification is constant-time to prevent timing attacks
"""

import bcrypt


def hash_password(password: str) -> str:
    """Hash a password using bcrypt.

    Args:
        password: The plain-text password to hash

    Returns:
        A bcrypt hash string

    Raises:
        TypeError: If password is not a string
        AttributeError: If password is None

    Note:
        Bcrypt has a 72-byte limit. Passwords longer than 72 bytes are
        automatically truncated before hashing.
    """
    # Convert password to bytes (truncated to 72 bytes for bcrypt)
    password_bytes = password.encode("utf-8")[:72]
    # Generate salt and hash
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    # Return as string
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a bcrypt hash.

    This function performs constant-time comparison to prevent timing attacks.

    Args:
        plain_password: The plain-text password to verify
        hashed_password: The bcrypt hash to verify against

    Returns:
        True if the password matches the hash, False otherwise

    Note:
        Returns False (does not raise) for malformed hashes or invalid inputs
        to handle database corruption or migration scenarios gracefully.
    """
    try:
        # Convert to bytes (truncated to 72 bytes for bcrypt)
        password_bytes = plain_password.encode("utf-8")[:72]
        hash_bytes = hashed_password.encode("utf-8")
        # Verify with constant-time comparison
        return bcrypt.checkpw(password_bytes, hash_bytes)
    except (ValueError, AttributeError, TypeError):
        # Malformed hash or invalid input (including None) - return False instead of raising
        return False
