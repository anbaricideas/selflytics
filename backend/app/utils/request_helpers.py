"""Request helper utilities for common request handling patterns."""

from fastapi import Request


def is_browser_request(request: Request) -> bool:
    """Detect if request is from a browser vs an API client.

    Browser requests are identified by:
    1. Accept header containing "text/html" (standard browser request)
    2. HX-Request header set to "true" (HTMX request)

    Args:
        request: FastAPI request object

    Returns:
        True if request is from a browser/HTMX, False for API requests
    """
    accept_header = request.headers.get("accept", "")
    # Starlette headers are case-insensitive for retrieval
    hx_request = request.headers.get("HX-Request", "") == "true"
    return "text/html" in accept_header or hx_request
