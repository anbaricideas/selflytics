"""Unit tests for CSRF protection.

These tests verify the CSRF token generation functionality works correctly.
They use the global CSRF configuration from the app instead of overriding it,
to avoid polluting the global state and breaking integration tests.
"""

from fastapi_csrf_protect import CsrfProtect


def test_csrf_token_generation():
    """Test that CSRF tokens are generated correctly."""
    # Use the app's global CSRF configuration (don't override it)
    csrf_protect = CsrfProtect()
    token1, signed1 = csrf_protect.generate_csrf_tokens()
    token2, signed2 = csrf_protect.generate_csrf_tokens()

    # Tokens should be unique
    assert token1 != token2
    assert signed1 != signed2

    # Tokens should have sufficient entropy (min 32 chars)
    assert len(token1) >= 32
    assert len(signed1) >= 32


def test_csrf_tokens_are_strings():
    """Test that tokens are string type."""
    # Use the app's global CSRF configuration (don't override it)
    csrf_protect = CsrfProtect()
    token, signed_token = csrf_protect.generate_csrf_tokens()

    assert isinstance(token, str)
    assert isinstance(signed_token, str)
