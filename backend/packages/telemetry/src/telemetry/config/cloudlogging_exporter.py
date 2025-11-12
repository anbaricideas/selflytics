"""Cloud Logging span exporter for OpenTelemetry - writes trace spans to Google Cloud Logging."""

import contextlib
import logging
from collections.abc import Sequence

from google.cloud import logging as cloud_logging
from opentelemetry.sdk.trace import ReadableSpan
from opentelemetry.sdk.trace.export import SpanExporter, SpanExportResult


class CloudLoggingSpanExporter(SpanExporter):
    """Custom OpenTelemetry span exporter that writes spans to Google Cloud Logging.

    This exporter sends OpenTelemetry Span objects to Cloud Logging with full
    trace context, enabling distributed tracing and session-based debugging.

    Handles errors gracefully to prevent span export failures from affecting
    application performance.

    Args:
        project_id: GCP project ID where spans will be written
        environment: Environment name (dev/staging/prod) for log segregation
        log_name: Optional custom log name (defaults to clinicraft-{environment})

    Example:
        >>> exporter = CloudLoggingSpanExporter(
        ...     project_id="my-gcp-project",
        ...     environment="dev"
        ... )
        >>> result = exporter.export([span])
        >>> exporter.shutdown()
    """

    def __init__(
        self,
        project_id: str,
        environment: str = "dev",
        log_name: str | None = None,
    ):
        if not project_id:
            raise ValueError("project_id cannot be empty")

        self._project_id = project_id
        self._environment = environment
        self._log_name = log_name or f"clinicraft-{environment}"

        # Lazy initialization - defer client creation until first export
        # This ensures Application Default Credentials are available (Cloud Run injects them post-startup)
        self._client = None
        self._logger = None
        self._shutdown = False

    def _ensure_client(self) -> None:
        """Lazily initialize Cloud Logging client on first use.

        Defers client creation until first export to ensure Application Default
        Credentials are available (important for Cloud Run environments where
        credentials are injected after container startup).
        """
        if self._client is None:
            self._client = cloud_logging.Client(project=self._project_id)
            self._logger = self._client.logger(self._log_name)

    def export(self, batch: Sequence[ReadableSpan]) -> SpanExportResult:
        """Export spans to Cloud Logging with full trace context.

        Each span is sent to Cloud Logging with all OpenTelemetry fields including
        trace context, timestamps, attributes, and status. Errors are logged but
        don't crash the application.

        Args:
            batch: Sequence of ReadableSpan objects to export

        Returns:
            SpanExportResult.SUCCESS if export succeeded
            SpanExportResult.FAILURE if export failed or exporter is shutdown
        """
        if self._shutdown:
            return SpanExportResult.FAILURE

        if not batch:
            return SpanExportResult.SUCCESS

        # Ensure client is initialized before first export
        self._ensure_client()

        try:
            for span in batch:
                # Format trace and span IDs
                trace_id = format(span.context.trace_id, "032x")
                span_id = format(span.context.span_id, "016x")
                trace = f"projects/{self._project_id}/traces/{trace_id}"

                # Build structured payload
                payload = {
                    "span_name": span.name,
                    "trace_id": trace_id,
                    "span_id": span_id,
                    "parent_span_id": (
                        format(span.parent.span_id, "016x") if span.parent else None
                    ),
                    "start_time": span.start_time,
                    "end_time": span.end_time,
                    "duration_ns": span.end_time - span.start_time if span.end_time else None,
                    "kind": span.kind.name if span.kind else None,
                    "status": span.status.status_code.name if span.status else None,
                    "attributes": dict(span.attributes) if span.attributes else {},
                    "environment": self._environment,
                    "source": "backend",
                }

                # Write to Cloud Logging
                self._logger.log_struct(
                    payload,
                    severity="INFO",
                    trace=trace,
                    span_id=span_id,
                )

            return SpanExportResult.SUCCESS

        except Exception as e:
            logging.warning("Failed to export spans to Cloud Logging: %s", e)
            return SpanExportResult.FAILURE

    def shutdown(self) -> None:
        """Shutdown the exporter and release resources.

        Sets shutdown flag to prevent further exports and explicitly closes
        the Cloud Logging client for defensive resource management.
        """
        self._shutdown = True
        # Explicitly close client for defensive resource cleanup
        if hasattr(self._client, "close"):
            with contextlib.suppress(Exception):
                self._client.close()

    def force_flush(self, timeout_millis: int = 30000) -> bool:  # noqa: ARG002
        """Force flush any buffered spans.

        Cloud Logging client automatically handles flushing, so this is primarily
        for interface compatibility.

        Args:
            timeout_millis: Maximum time to wait for flush (unused)

        Returns:
            True if flush succeeded, False if exporter is shutdown
        """
        return not self._shutdown
