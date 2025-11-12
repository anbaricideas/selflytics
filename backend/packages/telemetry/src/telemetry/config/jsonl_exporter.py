"""JSONL span exporter for OpenTelemetry - writes trace spans to JSONL files."""

import contextlib
import logging
import threading
from collections.abc import Sequence
from pathlib import Path
from typing import TextIO

from opentelemetry.sdk.trace import ReadableSpan
from opentelemetry.sdk.trace.export import SpanExporter, SpanExportResult

from .models import InstrumentationScope, SpanContext, SpanData, SpanEvent, SpanLink, SpanStatus


class JSONLSpanExporter(SpanExporter):
    """Custom OpenTelemetry span exporter that writes spans to JSONL files.

    This exporter serializes OpenTelemetry Span objects to JSON Lines format
    (one JSON object per line), suitable for local development and debugging.

    Thread-safe for concurrent exports from multiple request handlers.

    Args:
        session_id: Unique identifier for this telemetry session (used as filename)
        log_path: Directory path where JSONL files will be written (default: ./logs)
        log_file_handle: Optional external file handle to write to (if provided,
            exporter will not close it on shutdown)

    Example:
        >>> exporter = JSONLSpanExporter(session_id="session-123", log_path="./logs")
        >>> result = exporter.export([span])
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

    def export(self, batch: Sequence[ReadableSpan]) -> SpanExportResult:
        """Export a batch of spans to JSONL file.

        Each span is serialized to a single JSON object and written as one line.
        All OpenTelemetry Span fields are included: name, timestamps, trace context,
        span kind, status, attributes, events, links, and resource.

        Thread-safe: Uses internal lock to prevent concurrent write corruption.

        Args:
            batch: Sequence of ReadableSpan objects to export

        Returns:
            SpanExportResult.SUCCESS if export succeeded
            SpanExportResult.FAILURE if export failed (e.g., after shutdown)
        """
        if self._shutdown:
            return SpanExportResult.FAILURE

        if not batch:
            return SpanExportResult.SUCCESS

        try:
            with self._lock:
                for span in batch:
                    # Convert OpenTelemetry span to Pydantic model for proper JSON serialization
                    span_data = SpanData(
                        name=span.name,
                        context=SpanContext(
                            trace_id=format(span.context.trace_id, "032x"),
                            span_id=format(span.context.span_id, "016x"),
                            trace_flags=span.context.trace_flags,
                        ),
                        parent_span_id=format(span.parent.span_id, "016x") if span.parent else None,
                        start_time=span.start_time,
                        end_time=span.end_time,
                        kind=span.kind.value if span.kind else None,
                        status=SpanStatus(
                            status_code=span.status.status_code.value if span.status else None,
                            description=span.status.description if span.status else None,
                        ),
                        attributes=dict(span.attributes) if span.attributes else {},
                        events=[
                            SpanEvent(
                                name=event.name,
                                timestamp=event.timestamp,
                                attributes=dict(event.attributes) if event.attributes else {},
                            )
                            for event in (span.events or [])
                        ],
                        links=[
                            SpanLink(
                                context=SpanContext(
                                    trace_id=format(link.context.trace_id, "032x"),
                                    span_id=format(link.context.span_id, "016x"),
                                    trace_flags=link.context.trace_flags,
                                ),
                                attributes=dict(link.attributes) if link.attributes else {},
                            )
                            for link in (span.links or [])
                        ],
                        resource=dict(span.resource.attributes) if span.resource else {},
                        instrumentation_scope=InstrumentationScope(
                            name=span.instrumentation_scope.name
                            if span.instrumentation_scope
                            else None,
                            version=span.instrumentation_scope.version
                            if span.instrumentation_scope
                            else None,
                        ),
                    )

                    # Use Pydantic's JSON serialization (handles datetime, bytes, enums)
                    json_line = span_data.model_dump_json()
                    self._log_file_handle.write(json_line + "\n")
                    self._log_file_handle.flush()

            return SpanExportResult.SUCCESS

        except Exception as e:
            # Log export errors for debugging (disk full, permissions, etc.)
            logging.warning("Failed to export spans: %s", e)
            return SpanExportResult.FAILURE

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
        """Force flush any buffered spans.

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
