"""JSONL log exporter for OpenTelemetry - writes log records to JSONL files."""

import contextlib
import logging
import threading
from collections.abc import Sequence
from pathlib import Path
from typing import TextIO

from opentelemetry.sdk._logs import LogData as OTelLogData
from opentelemetry.sdk._logs.export import LogExporter, LogExportResult

from .models import InstrumentationScope, LogData


class JSONLLogExporter(LogExporter):
    """Custom OpenTelemetry log exporter that writes log records to JSONL files.

    This exporter serializes OpenTelemetry LogRecord objects to JSON Lines format
    (one JSON object per line), suitable for local development and debugging.

    Thread-safe for concurrent exports from multiple request handlers.

    Args:
        session_id: Unique identifier for this telemetry session (used as filename)
        log_path: Directory path where JSONL files will be written (default: ./logs)
        log_file_handle: Optional external file handle to write to (if provided,
            exporter will not close it on shutdown)

    Example:
        >>> exporter = JSONLLogExporter(session_id="session-123", log_path="./logs")
        >>> result = exporter.export([log_data])
        >>> exporter.shutdown()
    """

    def __init__(
        self,
        session_id: str,
        log_path: str = "./logs",
        log_file_handle: TextIO | None = None,
    ):
        if not session_id:
            raise ValueError("session_id cannot be empty")

        self._session_id = session_id
        self._log_path = Path(log_path).resolve()
        self._log_file_path = self._log_path / f"{session_id}.jsonl"
        self._lock = threading.Lock()
        self._log_file_handle = log_file_handle or self._open_log_file()
        self._owns_file_handle = log_file_handle is None
        self._shutdown = False

    def _open_log_file(self) -> TextIO:
        """Create log directory and open log file for appending.

        Returns:
            File handle opened in append mode with UTF-8 encoding.
        """
        self._log_path.mkdir(parents=True, exist_ok=True)
        return self._log_file_path.open("a", encoding="utf-8")

    def export(self, batch: Sequence[OTelLogData]) -> LogExportResult:
        """Export a batch of log records to JSONL file.

        Each log record is serialized to a single JSON object and written as one line.
        All OpenTelemetry LogRecord fields are included: timestamp, severity, body,
        trace context, attributes, resource, and instrumentation scope.

        Thread-safe: Uses internal lock to prevent concurrent write corruption.

        Args:
            batch: Sequence of LogData objects to export

        Returns:
            LogExportResult.SUCCESS if export succeeded
            LogExportResult.FAILURE if export failed (e.g., after shutdown)
        """
        if self._shutdown:
            return LogExportResult.FAILURE

        if not batch:
            return LogExportResult.SUCCESS

        try:
            with self._lock:
                for otel_log_data in batch:
                    log_record = otel_log_data.log_record

                    # Convert OpenTelemetry log to Pydantic model for proper JSON serialization
                    log_data = LogData(
                        timestamp=log_record.timestamp,
                        observed_timestamp=log_record.observed_timestamp,
                        trace_id=format(log_record.trace_id, "032x")
                        if log_record.trace_id
                        else None,
                        span_id=format(log_record.span_id, "016x") if log_record.span_id else None,
                        trace_flags=log_record.trace_flags,
                        severity_text=log_record.severity_text,
                        severity_number=log_record.severity_number,
                        body=log_record.body,
                        attributes=dict(log_record.attributes) if log_record.attributes else {},
                        resource=dict(log_record.resource.attributes)
                        if log_record.resource
                        else {},
                        scope=InstrumentationScope(
                            name=otel_log_data.instrumentation_scope.name,
                            version=otel_log_data.instrumentation_scope.version,
                        )
                        if otel_log_data.instrumentation_scope
                        else InstrumentationScope(),
                    )

                    # Use Pydantic's JSON serialization (handles datetime, bytes, enums)
                    json_line = log_data.model_dump_json()
                    self._log_file_handle.write(json_line + "\n")
                    self._log_file_handle.flush()

            return LogExportResult.SUCCESS

        except Exception as e:
            # Log export errors for debugging (disk full, permissions, etc.)
            logging.warning("Failed to export log records: %s", e)
            return LogExportResult.FAILURE

    def shutdown(self) -> None:
        """Shutdown the exporter and release resources.

        If the exporter owns the file handle (not externally provided), it will
        be closed. External file handles are not closed, allowing the caller to
        manage the lifecycle.
        """
        self._shutdown = True

        if self._owns_file_handle and self._log_file_handle:
            with contextlib.suppress(Exception):
                self._log_file_handle.close()

    def force_flush(self, _timeout_millis: int = 30000) -> bool:
        """Force flush any buffered log records.

        Args:
            _timeout_millis: Maximum time to wait for flush (unused, provided for interface compatibility)

        Returns:
            True if flush succeeded, False otherwise
        """
        if self._shutdown:
            return False

        try:
            with self._lock:
                if self._log_file_handle:
                    self._log_file_handle.flush()
            return True
        except Exception:
            return False
