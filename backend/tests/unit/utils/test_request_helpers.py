"""Unit tests for request helper utilities."""

import pytest
from fastapi import Request

from app.utils.request_helpers import is_browser_request


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
            "headers": [[k.lower().encode(), v.encode()] for k, v in headers.items()],
        }
        return Request(scope)

    return _create_request


def test_is_browser_request_with_html_accept_header(mock_request):
    """Test that requests with text/html in Accept header are detected as browser requests."""
    request = mock_request(accept_header="text/html,application/xhtml+xml,application/xml")
    assert is_browser_request(request) is True


def test_is_browser_request_with_hx_request_header(mock_request):
    """Test that HTMX requests are detected as browser requests."""
    request = mock_request(hx_request="true")
    assert is_browser_request(request) is True


def test_is_browser_request_with_both_headers(mock_request):
    """Test that requests with both html accept and HX-Request are detected as browser requests."""
    request = mock_request(accept_header="text/html", hx_request="true")
    assert is_browser_request(request) is True


def test_is_browser_request_with_json_accept_header(mock_request):
    """Test that API requests with application/json are not detected as browser requests."""
    request = mock_request(accept_header="application/json")
    assert is_browser_request(request) is False


def test_is_browser_request_with_no_headers(mock_request):
    """Test that requests with no relevant headers are not detected as browser requests."""
    request = mock_request()
    assert is_browser_request(request) is False


def test_is_browser_request_with_hx_request_false(mock_request):
    """Test that HX-Request: false is not detected as browser request."""
    request = mock_request(hx_request="false")
    assert is_browser_request(request) is False


def test_is_browser_request_with_partial_html_match(mock_request):
    """Test that accept header with text/html substring is detected."""
    request = mock_request(accept_header="application/json,text/html;q=0.9")
    assert is_browser_request(request) is True
