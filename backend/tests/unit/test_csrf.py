"""Unit tests for CSRF protection."""

from fastapi_csrf_protect import CsrfProtect
from pydantic import BaseModel


class CsrfSettingsForTest(BaseModel):
    """CSRF settings for testing."""

    secret_key: str = "test-secret-key-min-32-chars-long"  # noqa: S105


def test_csrf_token_generation():
    """Test that CSRF tokens are generated correctly."""

    # Configure CSRF with test settings
    @CsrfProtect.load_config
    def get_csrf_config():
        return CsrfSettingsForTest()

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

    # Configure CSRF with test settings
    @CsrfProtect.load_config
    def get_csrf_config():
        return CsrfSettingsForTest()

    csrf_protect = CsrfProtect()
    token, signed_token = csrf_protect.generate_csrf_tokens()

    assert isinstance(token, str)
    assert isinstance(signed_token, str)
