"""Unit tests for application configuration."""

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
