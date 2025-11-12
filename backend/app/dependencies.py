"""Shared dependencies for FastAPI routes."""

from datetime import datetime
from pathlib import Path

from fastapi.templating import Jinja2Templates


def format_datetime(dt: datetime | None, fmt: str = "%Y-%m-%d %H:%M") -> str:
    """Jinja2 filter for consistent datetime formatting.

    Args:
        dt: datetime object to format (can be None)
        fmt: strftime format string (default: "YYYY-MM-DD HH:MM")

    Returns:
        Formatted datetime string, or "N/A" if dt is None

    Usage in templates:
        {{ activity.date | datetime }}
        {{ activity.date | datetime("%Y-%m-%d") }}
    """
    return dt.strftime(fmt) if dt else "N/A"


# Single shared Jinja2Templates instance for the application
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")

# Register custom Jinja2 filters
templates.env.filters["datetime"] = format_datetime


def get_templates() -> Jinja2Templates:
    """Dependency to provide Jinja2Templates instance to routes.

    Returns the shared templates instance to avoid redundant template loading.
    """
    return templates
