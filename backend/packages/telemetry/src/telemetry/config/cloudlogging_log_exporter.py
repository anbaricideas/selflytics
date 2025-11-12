"""Cloud Logging log exporter for OpenTelemetry - writes log records to Google Cloud Logging."""

import contextlib
import logging
from collections.abc import Sequence

from google.cloud import logging as cloud_logging
from opentelemetry._logs import SeverityNumber
from opentelemetry.sdk._logs import LogData
from opentelemetry.sdk._logs.export import LogExporter, LogExportResult


class CloudLoggingLogExporter(LogExporter):
    """Custom OpenTelemetry log exporter that writes log records to Google Cloud Logging.

    This exporter sends OpenTelemetry LogRecord objects to Cloud Logging with proper
    trace correlation, enabling distributed tracing and cloud-native observability.

    Handles errors gracefully to prevent log export failures from affecting application
    performance.

    Args:
        project_id: GCP project ID where logs will be written
        environment: Environment name (dev/staging/prod) for log segregation
        log_name: Optional custom log name (defaults to clinicraft-{environment})

    Example:
        >>> exporter = CloudLoggingLogExporter(
        ...     project_id="my-gcp-project",
        ...     environment="dev"
        ... )
        >>> result = exporter.export([log_data])
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

    def _map_severity(self, severity_number: SeverityNumber | int) -> str:
        """Map OpenTelemetry severity to Cloud Logging severity.

        Args:
            severity_number: OpenTelemetry severity number (1-24)

        Returns:
            Cloud Logging severity string (DEBUG/INFO/WARNING/ERROR/CRITICAL)
        """
        # Convert SeverityNumber enum to int if needed
        if isinstance(severity_number, SeverityNumber):
            severity_value = severity_number.value
        else:
            severity_value = severity_number

        # Defensive: handle invalid severity values
        if severity_value < 1:
            severity_value = 9  # Default to INFO
        elif severity_value > 24:
            severity_value = 24  # Cap at FATAL

        # Map OpenTelemetry severity ranges to Cloud Logging severities
        # TRACE (1-4) + DEBUG (5-8) -> DEBUG
        if severity_value <= 8:
            return "DEBUG"
        # INFO (9-12) -> INFO
        if severity_value <= 12:
            return "INFO"
        # WARN (13-16) -> WARNING
        if severity_value <= 16:
            return "WARNING"
        # ERROR (17-20) -> ERROR
        if severity_value <= 20:
            return "ERROR"
        # FATAL (21-24) -> CRITICAL
        return "CRITICAL"

    def export(self, batch: Sequence[LogData]) -> LogExportResult:
        """Export log records to Cloud Logging with trace correlation.

        Each log record is sent to Cloud Logging with proper trace context for
        distributed tracing. Errors are logged but don't crash the application.

        Args:
            batch: Sequence of LogData objects to export

        Returns:
            LogExportResult.SUCCESS if export succeeded
            LogExportResult.FAILURE if export failed or exporter is shutdown
        """
        if self._shutdown:
            return LogExportResult.FAILURE

        if not batch:
            return LogExportResult.SUCCESS

        # Ensure client is initialized before first export
        self._ensure_client()

        try:
            for log_data in batch:
                log_record = log_data.log_record

                # Format trace for Cloud Logging (projects/PROJECT_ID/traces/TRACE_ID)
                trace_id = format(log_record.trace_id, "032x") if log_record.trace_id else None
                trace = f"projects/{self._project_id}/traces/{trace_id}" if trace_id else None

                # Format span ID (16-char hex)
                span_id = format(log_record.span_id, "016x") if log_record.span_id else None

                # Build JSON payload with log message and attributes
                payload = {
                    "message": log_record.body,
                    "trace_id": trace_id,
                    "span_id": span_id,
                    "source": "backend",
                    "environment": self._environment,
                }

                # Merge log attributes into payload
                if log_record.attributes:
                    payload.update(dict(log_record.attributes))

                # Map OpenTelemetry severity to Cloud Logging severity
                severity = self._map_severity(log_record.severity_number)

                # Write to Cloud Logging with trace correlation
                self._logger.log_struct(
                    payload,
                    severity=severity,
                    trace=trace,
                    span_id=span_id,
                )

            return LogExportResult.SUCCESS

        except Exception as e:
            logging.warning("Failed to export logs to Cloud Logging: %s", e)
            return LogExportResult.FAILURE

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
        """Force flush any buffered log records.

        Cloud Logging client automatically handles flushing, so this is primarily
        for interface compatibility.

        Args:
            timeout_millis: Maximum time to wait for flush (unused)

        Returns:
            True if flush succeeded, False if exporter is shutdown
        """
        return not self._shutdown
