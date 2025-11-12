"""Telemetry middleware for request tracing."""

import logging
import time
from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from opentelemetry import trace
from starlette.middleware.base import BaseHTTPMiddleware


logger = logging.getLogger(__name__)


class TelemetryMiddleware(BaseHTTPMiddleware):
    """
    Middleware to capture telemetry for all HTTP requests.

    Logs request/response information with trace correlation (trace_id, span_id)
    and measures request duration for performance analysis.

    Attributes:
        skip_paths: Set of paths to skip logging (e.g., health checks to reduce noise)
    """

    def __init__(self, app, skip_paths: set[str] | None = None):
        """
        Initialize telemetry middleware.

        Args:
            app: FastAPI application
            skip_paths: Optional set of paths to skip logging (e.g., {"/health"})
        """
        super().__init__(app)
        self.skip_paths = skip_paths or set()

    def _get_trace_context(self) -> tuple[str | None, str | None]:
        """
        Extract trace_id and span_id from current OpenTelemetry context.

        Returns:
            Tuple of (trace_id, span_id) as hex strings, or (None, None) if no active span
        """
        span = trace.get_current_span()
        span_context = span.get_span_context()

        if span_context.is_valid:
            trace_id = format(span_context.trace_id, "032x")
            span_id = format(span_context.span_id, "016x")
            return trace_id, span_id

        return None, None

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """
        Process request and capture telemetry.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware/route handler

        Returns:
            HTTP response
        """
        # Skip telemetry for certain paths (e.g., health checks)
        if request.url.path in self.skip_paths:
            return await call_next(request)

        # Extract trace context for correlation
        trace_id, span_id = self._get_trace_context()

        # Log request start
        logger.info(
            "Request started",
            extra={
                "method": request.method,
                "path": request.url.path,
                "trace_id": trace_id,
                "span_id": span_id,
            },
        )

        # Measure request duration
        start_time = time.perf_counter()

        try:
            # Process request
            response = await call_next(request)

            # Calculate duration
            duration_ms = (time.perf_counter() - start_time) * 1000

            # Log request completion
            logger.info(
                "Request completed",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration_ms": round(duration_ms, 2),
                    "trace_id": trace_id,
                    "span_id": span_id,
                },
            )

            return response

        except Exception as exc:
            # Calculate duration even for exceptions
            duration_ms = (time.perf_counter() - start_time) * 1000

            # Log request exception
            logger.error(
                "Request failed",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "duration_ms": round(duration_ms, 2),
                    "trace_id": trace_id,
                    "span_id": span_id,
                    "error": str(exc),
                },
                exc_info=True,
            )

            # Re-raise exception for FastAPI to handle
            raise
