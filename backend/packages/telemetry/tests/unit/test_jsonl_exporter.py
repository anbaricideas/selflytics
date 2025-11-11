"""Tests for JSONL span exporter - writes OpenTelemetry spans to JSONL files."""

import json
import tempfile
import threading
from pathlib import Path

import pytest
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SpanExportResult
from opentelemetry.trace import SpanKind
from telemetry.config.jsonl_exporter import JSONLSpanExporter


@pytest.fixture
def sample_span():
    """Create a real OpenTelemetry span for testing."""
    resource = Resource.create({"service.name": "test-service", "service.version": "1.0.0"})

    # Create a tracer provider with the resource
    tracer_provider = TracerProvider(resource=resource)
    tracer = tracer_provider.get_tracer("test.tracer", "1.0.0")

    # Create a real span using the tracer
    with tracer.start_as_current_span(
        "test_operation",
        kind=SpanKind.INTERNAL,
        attributes={"http.method": "GET", "http.url": "/test"},
    ) as span:
        span.set_attribute("custom.key", "custom.value")
        # Span will be readable after context exits

    # Get the completed span (it's now a ReadableSpan)
    return span


class TestJSONLSpanExporterInitialization:
    """Tests for JSONLSpanExporter initialization."""

    def test_initializes_with_session_id(self):
        """Test that exporter can be initialized with a session id."""
        with tempfile.TemporaryDirectory() as temp_dir:
            exporter = JSONLSpanExporter(session_id="test-session-123", log_path=temp_dir)
            assert exporter is not None

    def test_raises_error_for_empty_session_id(self):
        """Test that empty session_id raises ValueError."""
        with (
            tempfile.TemporaryDirectory() as temp_dir,
            pytest.raises(ValueError, match="session_id cannot be empty"),
        ):
            JSONLSpanExporter(session_id="", log_path=temp_dir)

    def test_creates_log_directory_if_missing(self):
        """Test that exporter creates log directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_path = Path(temp_dir) / "nested" / "logs"
            assert not log_path.exists()

            exporter = JSONLSpanExporter(session_id="test-123", log_path=str(log_path))

            assert log_path.exists()
            exporter.shutdown()

    def test_creates_log_file_with_session_id(self):
        """Test that exporter creates log file named after session_id."""
        with tempfile.TemporaryDirectory() as temp_dir:
            session_id = "test-session-456"
            exporter = JSONLSpanExporter(session_id=session_id, log_path=temp_dir)

            expected_file = Path(temp_dir) / f"{session_id}.jsonl"
            assert expected_file.exists()
            exporter.shutdown()

    def test_accepts_external_file_handle(self):
        """Test that exporter can accept an external file handle."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "custom.jsonl"
            with log_file.open("w", encoding="utf-8") as f:
                exporter = JSONLSpanExporter(
                    session_id="test-789", log_path=temp_dir, log_file_handle=f
                )

                assert exporter is not None
                # Exporter should not close external handle
                assert not f.closed

            # File should be closed by context manager, not exporter
            assert f.closed


class TestJSONLSpanExporterSerialization:
    """Tests for JSONL serialization format and correctness."""

    def test_serializes_span_with_all_fields(self, sample_span):
        """Test that all Span fields are correctly serialized to JSONL."""
        with tempfile.TemporaryDirectory() as temp_dir:
            exporter = JSONLSpanExporter(session_id="test-export", log_path=temp_dir)

            result = exporter.export([sample_span])

            assert result == SpanExportResult.SUCCESS

            # Verify file contents with all expected fields
            log_file = Path(temp_dir) / "test-export.jsonl"
            with log_file.open(encoding="utf-8") as f:
                line = f.readline()
                data = json.loads(line)

                # Verify core fields
                assert "name" in data
                assert data["name"] == "test_operation"
                assert "start_time" in data
                assert "end_time" in data

                # Verify trace context
                assert "context" in data
                assert "span_id" in data["context"]
                assert "trace_id" in data["context"]
                assert "trace_flags" in data["context"]
                assert "parent_span_id" in data

                # Verify span kind
                assert "kind" in data
                assert data["kind"] == SpanKind.INTERNAL.value

                # Verify status
                assert "status" in data

                # Verify attributes
                assert "attributes" in data
                assert "http.method" in data["attributes"]
                assert data["attributes"]["http.method"] == "GET"

                # Verify resource information
                assert "resource" in data
                assert data["resource"]["service.name"] == "test-service"

            exporter.shutdown()

    def test_jsonl_format_compliance(self, sample_span):
        """Test that output is valid JSONL (one JSON object per line)."""
        with tempfile.TemporaryDirectory() as temp_dir:
            exporter = JSONLSpanExporter(session_id="test-jsonl", log_path=temp_dir)

            # Export multiple spans
            exporter.export([sample_span, sample_span, sample_span])

            log_file = Path(temp_dir) / "test-jsonl.jsonl"
            with log_file.open(encoding="utf-8") as f:
                content = f.read()

            # Verify JSONL format
            lines = content.strip().split("\n")
            assert len(lines) == 3

            # Each line should be independently parseable as JSON
            for line in lines:
                data = json.loads(line)  # Should not raise
                assert isinstance(data, dict)
                assert "name" in data
                assert "context" in data
                assert "span_id" in data["context"]

            exporter.shutdown()


class TestJSONLSpanExporterExport:
    """Tests for JSONLSpanExporter export functionality."""

    def test_exports_single_span(self, sample_span):
        """Test that exporter writes a single span to JSONL."""
        with tempfile.TemporaryDirectory() as temp_dir:
            exporter = JSONLSpanExporter(session_id="test-single", log_path=temp_dir)

            result = exporter.export([sample_span])

            assert result == SpanExportResult.SUCCESS

            # Verify file exists and has content
            log_file = Path(temp_dir) / "test-single.jsonl"
            assert log_file.exists()

            with log_file.open(encoding="utf-8") as f:
                lines = f.readlines()
                assert len(lines) == 1

            exporter.shutdown()

    def test_exports_empty_batch(self):
        """Test that exporter handles empty batch gracefully."""
        with tempfile.TemporaryDirectory() as temp_dir:
            exporter = JSONLSpanExporter(session_id="test-empty", log_path=temp_dir)

            result = exporter.export([])

            assert result == SpanExportResult.SUCCESS
            exporter.shutdown()


class TestJSONLSpanExporterThreadSafety:
    """Tests for thread-safety of JSONLSpanExporter."""

    def test_concurrent_exports_are_thread_safe(self, sample_span):
        """Test that concurrent exports don't corrupt the log file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            exporter = JSONLSpanExporter(session_id="test-concurrent", log_path=temp_dir)

            def export_spans(_thread_id: int, count: int):
                for _i in range(count):
                    exporter.export([sample_span])

            # Create multiple threads writing concurrently
            threads = []
            for tid in range(5):
                thread = threading.Thread(target=export_spans, args=(tid, 10))
                threads.append(thread)
                thread.start()

            # Wait for all threads to complete
            for thread in threads:
                thread.join()

            exporter.shutdown()

            # Verify all 50 spans were written (5 threads x 10 spans)
            log_file = Path(temp_dir) / "test-concurrent.jsonl"
            with log_file.open(encoding="utf-8") as f:
                lines = f.readlines()
                assert len(lines) == 50

                # Verify all lines are valid JSON
                for line in lines:
                    data = json.loads(line)
                    assert "name" in data
                    assert data["name"] == "test_operation"


class TestJSONLSpanExporterShutdown:
    """Tests for JSONLSpanExporter shutdown behavior."""

    def test_shutdown_closes_file_handle(self):
        """Test that shutdown closes the file handle."""
        with tempfile.TemporaryDirectory() as temp_dir:
            exporter = JSONLSpanExporter(session_id="test-shutdown", log_path=temp_dir)

            # Access the internal file handle
            file_handle = exporter._log_file_handle

            exporter.shutdown()

            # File should be closed after shutdown
            assert file_handle.closed

    def test_shutdown_does_not_close_external_handle(self):
        """Test that shutdown doesn't close externally provided file handle."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "external.jsonl"
            with log_file.open("w", encoding="utf-8") as f:
                exporter = JSONLSpanExporter(
                    session_id="test-external", log_path=temp_dir, log_file_handle=f
                )

                exporter.shutdown()

                # External handle should remain open
                assert not f.closed

    def test_exports_after_shutdown_fail_gracefully(self, sample_span):
        """Test that exports after shutdown return failure status."""
        with tempfile.TemporaryDirectory() as temp_dir:
            exporter = JSONLSpanExporter(session_id="test-fail", log_path=temp_dir)
            exporter.shutdown()

            result = exporter.export([sample_span])

            assert result == SpanExportResult.FAILURE
