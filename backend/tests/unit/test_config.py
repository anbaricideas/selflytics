"""Unit tests for application configuration."""

import pytest
from pydantic import ValidationError

from app.config import Settings


def test_csrf_secret_has_default():
    """Test that csrf_secret has a default value."""
    settings = Settings()
    assert settings.csrf_secret is not None
    assert len(settings.csrf_secret) >= 32


def test_csrf_secret_loaded_from_env(monkeypatch):
    """Test that csrf_secret can be loaded from environment."""
    test_secret = "test-csrf-secret-min-32-chars-long"  # noqa: S105
    monkeypatch.setenv("CSRF_SECRET", test_secret)
    settings = Settings()
    assert settings.csrf_secret == test_secret


def test_csrf_secret_rejects_short_secrets(monkeypatch):
    """Test that csrf_secret rejects secrets shorter than 32 characters."""
    short_secret = "too-short"  # noqa: S105
    monkeypatch.setenv("CSRF_SECRET", short_secret)
    with pytest.raises(ValidationError) as exc_info:
        Settings()
    assert "CSRF_SECRET must be at least 32 characters" in str(exc_info.value)
