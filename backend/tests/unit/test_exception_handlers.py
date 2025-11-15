"""Unit tests for main.py exception handlers."""

from unittest.mock import patch

import pytest
from fastapi import Request
from fastapi_csrf_protect.exceptions import CsrfProtectError

from app.main import csrf_protect_exception_handler


@pytest.fixture
def mock_request():
    """Create a mock request for testing."""

    def _create_request(accept_header: str | None = None, hx_request: str | None = None):
        """Create mock Request with specified headers."""
        headers = {}
        if accept_header is not None:
            headers["accept"] = accept_header
        if hx_request is not None:
            headers["hx-request"] = hx_request

        # Create a minimal mock Request
        # Note: Starlette expects header names in lowercase in the scope
        scope = {
            "type": "http",
            "method": "POST",
            "path": "/auth/login",
            "headers": [[k.lower().encode(), v.encode()] for k, v in headers.items()],
        }
        return Request(scope)

    return _create_request


@pytest.mark.asyncio
async def test_csrf_exception_handler_logs_warning_for_browser_requests(mock_request):
    """Test that CSRF validation failures are logged for browser requests."""
    request = mock_request(accept_header="text/html")
    exc = CsrfProtectError(status_code=403, message="CSRF token validation failed")

    # Mock the logger
    with patch("app.main.logger") as mock_logger:
        response = await csrf_protect_exception_handler(request, exc)

        # Verify logger.warning was called
        assert mock_logger.warning.called
        call_args = mock_logger.warning.call_args
        assert call_args is not None

        # Check the log message contains expected fields
        log_format = call_args[0][0]  # First positional arg is the format string
        assert "CSRF validation failed" in log_format
        assert "path=" in log_format
        assert "method=" in log_format
        assert "client=" in log_format

        # Verify response is HTML (status 403)
        assert response.status_code == 403


@pytest.mark.asyncio
async def test_csrf_exception_handler_logs_warning_for_htmx_requests(mock_request):
    """Test that CSRF validation failures are logged for HTMX requests."""
    request = mock_request(hx_request="true")
    exc = CsrfProtectError(status_code=403, message="CSRF token validation failed")

    # Mock the logger
    with patch("app.main.logger") as mock_logger:
        response = await csrf_protect_exception_handler(request, exc)

        # Verify logger.warning was called
        assert mock_logger.warning.called

        # Verify response is HTML fragment (status 403)
        assert response.status_code == 403


@pytest.mark.asyncio
async def test_csrf_exception_handler_logs_warning_for_api_requests(mock_request):
    """Test that CSRF validation failures are logged for API requests."""
    request = mock_request(accept_header="application/json")
    exc = CsrfProtectError(status_code=403, message="CSRF token validation failed")

    # Mock the logger
    with patch("app.main.logger") as mock_logger:
        response = await csrf_protect_exception_handler(request, exc)

        # Verify logger.warning was called
        assert mock_logger.warning.called

        # Verify response is JSON (status 403)
        assert response.status_code == 403
        assert response.headers["content-type"] == "application/json"


@pytest.mark.asyncio
async def test_csrf_exception_handler_redacts_client_ip():
    """Test that client IP is redacted in CSRF error logs."""
    # Create request with client info using a proper scope
    headers = {"accept": "text/html"}
    scope = {
        "type": "http",
        "method": "POST",
        "path": "/auth/login",
        "headers": [[k.lower().encode(), v.encode()] for k, v in headers.items()],
        "client": ("192.168.1.100", 12345),  # (host, port) tuple
    }
    request = Request(scope)

    exc = CsrfProtectError(status_code=403, message="CSRF token validation failed")

    # Mock both logger and redact function
    with (
        patch("app.main.logger") as mock_logger,
        patch("app.main.redact_for_logging") as mock_redact,
    ):
        mock_redact.return_value = "[REDACTED]"

        await csrf_protect_exception_handler(request, exc)

        # Verify redact_for_logging was called with the client IP
        mock_redact.assert_called_once_with("192.168.1.100")

        # Verify the redacted value was used in the log
        call_args = mock_logger.warning.call_args
        log_args = call_args[0][1:]  # Skip format string, get the values
        assert "[REDACTED]" in log_args
