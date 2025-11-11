"""Tests for JSONL log exporter - writes OpenTelemetry log records to JSONL files."""

import json
import tempfile
import threading
from pathlib import Path

import pytest
from opentelemetry.sdk._logs import LogData, LogRecord
from opentelemetry.sdk._logs.export import LogExportResult
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.util.instrumentation import InstrumentationScope
from telemetry.config.jsonl_log_exporter import JSONLLogExporter


@pytest.fixture
def sample_log_record():
    """Create a real OpenTelemetry log record for testing."""
    resource = Resource.create({"service.name": "test-service", "service.version": "1.0.0"})
    scope = InstrumentationScope("test.logger", "1.0.0")

    log_record = LogRecord(
        timestamp=1234567890000000000,
        observed_timestamp=1234567890000000000,
        trace_id=0x12345678901234567890123456789012,
        span_id=0x1234567890123456,
        trace_flags=0x01,
        severity_text="INFO",
        severity_number=9,
        body="Test log message",
        resource=resource,
        attributes={"key": "value", "user.id": "user-123"},
    )

    return LogData(log_record=log_record, instrumentation_scope=scope)


class TestJSONLLogExporterInitialization:
    """Tests for JSONLLogExporter initialization."""

    def test_initializes_with_session_id(self):
        """Test that exporter can be initialized with a session id."""
        with tempfile.TemporaryDirectory() as temp_dir:
            exporter = JSONLLogExporter(session_id="test-session-123", log_path=temp_dir)

            assert exporter is not None

    def test_raises_error_for_empty_session_id(self):
        """Test that empty session_id raises ValueError."""
        with (
            tempfile.TemporaryDirectory() as temp_dir,
            pytest.raises(ValueError, match="session_id cannot be empty"),
        ):
            JSONLLogExporter(session_id="", log_path=temp_dir)

    def test_creates_log_directory_if_missing(self):
        """Test that exporter creates log directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_path = Path(temp_dir) / "nested" / "logs"
            assert not log_path.exists()

            exporter = JSONLLogExporter(session_id="test-123", log_path=str(log_path))

            assert log_path.exists()
            exporter.shutdown()

    def test_creates_log_file_with_session_id(self):
        """Test that exporter creates log file named after session_id."""
        with tempfile.TemporaryDirectory() as temp_dir:
            session_id = "test-session-456"
            exporter = JSONLLogExporter(session_id=session_id, log_path=temp_dir)

            expected_file = Path(temp_dir) / f"{session_id}.jsonl"
            assert expected_file.exists()
            exporter.shutdown()

    def test_accepts_external_file_handle(self):
        """Test that exporter can accept an external file handle."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "custom.jsonl"
            with log_file.open("w", encoding="utf-8") as f:
                exporter = JSONLLogExporter(
                    session_id="test-789", log_path=temp_dir, log_file_handle=f
                )

                assert exporter is not None
                # Exporter should not close external handle
                assert not f.closed

            # File should be closed by context manager, not exporter
            assert f.closed


class TestJSONLLogExporterSerialization:
    """Tests for JSONL serialization format and correctness."""

    def test_serializes_log_record_with_all_fields(self, sample_log_record):
        """Test that all LogRecord fields are correctly serialized to JSONL."""
        with tempfile.TemporaryDirectory() as temp_dir:
            exporter = JSONLLogExporter(session_id="test-export", log_path=temp_dir)

            result = exporter.export([sample_log_record])

            assert result == LogExportResult.SUCCESS

            # Verify file contents with all expected fields
            log_file = Path(temp_dir) / "test-export.jsonl"
            with log_file.open(encoding="utf-8") as f:
                line = f.readline()
                data = json.loads(line)

                # Verify core fields
                assert data["timestamp"] == 1234567890000000000
                assert data["severity_text"] == "INFO"
                assert data["severity_number"] == 9
                assert data["body"] == "Test log message"

                # Verify trace context
                assert data["trace_id"] == "12345678901234567890123456789012"
                assert data["span_id"] == "1234567890123456"
                assert data["trace_flags"] == 1

                # Verify attributes
                assert data["attributes"]["key"] == "value"
                assert data["attributes"]["user.id"] == "user-123"

                # Verify resource information
                assert data["resource"]["service.name"] == "test-service"
                assert data["resource"]["service.version"] == "1.0.0"

                # Verify instrumentation scope
                assert data["scope"]["name"] == "test.logger"
                assert data["scope"]["version"] == "1.0.0"

            exporter.shutdown()

    def test_jsonl_format_compliance(self, sample_log_record):
        """Test that output is valid JSONL (one JSON object per line)."""
        with tempfile.TemporaryDirectory() as temp_dir:
            exporter = JSONLLogExporter(session_id="test-jsonl", log_path=temp_dir)

            # Export multiple records
            exporter.export([sample_log_record, sample_log_record, sample_log_record])

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
                assert "timestamp" in data
                assert "body" in data

            exporter.shutdown()


class TestJSONLLogExporterExport:
    """Tests for JSONLLogExporter export functionality."""

    def test_exports_single_log_record(self, sample_log_record):
        """Test that exporter writes a single log record to JSONL."""
        with tempfile.TemporaryDirectory() as temp_dir:
            exporter = JSONLLogExporter(session_id="test-single", log_path=temp_dir)

            result = exporter.export([sample_log_record])

            assert result == LogExportResult.SUCCESS

            # Verify file exists and has content
            log_file = Path(temp_dir) / "test-single.jsonl"
            assert log_file.exists()

            with log_file.open(encoding="utf-8") as f:
                lines = f.readlines()
                assert len(lines) == 1

            exporter.shutdown()

    def test_exports_multiple_log_records(self):
        """Test that exporter writes multiple log records in batch."""
        with tempfile.TemporaryDirectory() as temp_dir:
            exporter = JSONLLogExporter(session_id="test-batch", log_path=temp_dir)

            # Create multiple real log records
            resource = Resource.create({"service.name": "test"})
            scope = InstrumentationScope("test.logger")
            log_data_list = []

            for i in range(5):
                log_record = LogRecord(
                    timestamp=1234567890000000000 + i,
                    observed_timestamp=1234567890000000000 + i,
                    trace_id=0,
                    span_id=0,
                    trace_flags=0,
                    severity_text="INFO",
                    severity_number=9,
                    body=f"Log message {i}",
                    resource=resource,
                    attributes={},
                )
                log_data = LogData(log_record=log_record, instrumentation_scope=scope)
                log_data_list.append(log_data)

            result = exporter.export(log_data_list)

            assert result == LogExportResult.SUCCESS

            # Verify file has 5 lines with correct content
            log_file = Path(temp_dir) / "test-batch.jsonl"
            with log_file.open(encoding="utf-8") as f:
                lines = f.readlines()
                assert len(lines) == 5

                for i, line in enumerate(lines):
                    data = json.loads(line)
                    assert data["body"] == f"Log message {i}"
                    assert data["timestamp"] == 1234567890000000000 + i

            exporter.shutdown()

    def test_exports_empty_batch(self):
        """Test that exporter handles empty batch gracefully."""
        with tempfile.TemporaryDirectory() as temp_dir:
            exporter = JSONLLogExporter(session_id="test-empty", log_path=temp_dir)

            result = exporter.export([])

            assert result == LogExportResult.SUCCESS
            exporter.shutdown()

    def test_appends_to_existing_file(self):
        """Test that exporter appends to existing log file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            session_id = "test-append"
            resource = Resource.create({"service.name": "test"})
            scope = InstrumentationScope("test.logger")

            # First export
            exporter1 = JSONLLogExporter(session_id=session_id, log_path=temp_dir)
            log_record1 = LogRecord(
                timestamp=1000000000000000000,
                observed_timestamp=1000000000000000000,
                trace_id=0,
                span_id=0,
                trace_flags=0,
                severity_text="INFO",
                severity_number=9,
                body="First message",
                resource=resource,
                attributes={},
            )
            log_data1 = LogData(log_record=log_record1, instrumentation_scope=scope)
            exporter1.export([log_data1])
            exporter1.shutdown()

            # Second export (should append)
            exporter2 = JSONLLogExporter(session_id=session_id, log_path=temp_dir)
            log_record2 = LogRecord(
                timestamp=2000000000000000000,
                observed_timestamp=2000000000000000000,
                trace_id=0,
                span_id=0,
                trace_flags=0,
                severity_text="WARN",
                severity_number=13,
                body="Second message",
                resource=resource,
                attributes={},
            )
            log_data2 = LogData(log_record=log_record2, instrumentation_scope=scope)
            exporter2.export([log_data2])
            exporter2.shutdown()

            # Verify both messages are in file
            log_file = Path(temp_dir) / f"{session_id}.jsonl"
            with log_file.open(encoding="utf-8") as f:
                lines = f.readlines()
                assert len(lines) == 2
                data1 = json.loads(lines[0])
                data2 = json.loads(lines[1])
                assert data1["body"] == "First message"
                assert data2["body"] == "Second message"
                assert data1["severity_text"] == "INFO"
                assert data2["severity_text"] == "WARN"


class TestJSONLLogExporterThreadSafety:
    """Tests for thread-safety of JSONLLogExporter."""

    def test_concurrent_exports_are_thread_safe(self):
        """Test that concurrent exports don't corrupt the log file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            exporter = JSONLLogExporter(session_id="test-concurrent", log_path=temp_dir)
            resource = Resource.create({"service.name": "test"})
            scope = InstrumentationScope("test.logger")

            def export_logs(thread_id: int, count: int):
                for i in range(count):
                    log_record = LogRecord(
                        timestamp=1234567890000000000 + thread_id * 1000 + i,
                        observed_timestamp=1234567890000000000 + thread_id * 1000 + i,
                        trace_id=0,
                        span_id=0,
                        trace_flags=0,
                        severity_text="INFO",
                        severity_number=9,
                        body=f"Thread {thread_id} message {i}",
                        resource=resource,
                        attributes={"thread": thread_id},
                    )
                    log_data = LogData(log_record=log_record, instrumentation_scope=scope)
                    exporter.export([log_data])

            # Create multiple threads writing concurrently
            threads = []
            for tid in range(5):
                thread = threading.Thread(target=export_logs, args=(tid, 10))
                threads.append(thread)
                thread.start()

            # Wait for all threads to complete
            for thread in threads:
                thread.join()

            exporter.shutdown()

            # Verify all 50 messages were written (5 threads x 10 messages)
            log_file = Path(temp_dir) / "test-concurrent.jsonl"
            with log_file.open(encoding="utf-8") as f:
                lines = f.readlines()
                assert len(lines) == 50

                # Verify all lines are valid JSON and track messages by thread
                thread_messages = {i: [] for i in range(5)}
                for line in lines:
                    data = json.loads(line)
                    assert "body" in data
                    assert "thread" in data["attributes"]
                    thread_id = data["attributes"]["thread"]
                    thread_messages[thread_id].append(data["body"])

                # Verify each thread wrote exactly 10 messages
                for tid in range(5):
                    assert len(thread_messages[tid]) == 10


class TestJSONLLogExporterShutdown:
    """Tests for JSONLLogExporter shutdown behavior."""

    def test_shutdown_closes_file_handle(self):
        """Test that shutdown closes the file handle."""
        with tempfile.TemporaryDirectory() as temp_dir:
            exporter = JSONLLogExporter(session_id="test-shutdown", log_path=temp_dir)

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
                exporter = JSONLLogExporter(
                    session_id="test-external", log_path=temp_dir, log_file_handle=f
                )

                exporter.shutdown()

                # External handle should remain open
                assert not f.closed

    def test_exports_after_shutdown_fail_gracefully(self, sample_log_record):
        """Test that exports after shutdown return failure status."""
        with tempfile.TemporaryDirectory() as temp_dir:
            exporter = JSONLLogExporter(session_id="test-fail", log_path=temp_dir)
            exporter.shutdown()

            result = exporter.export([sample_log_record])

            assert result == LogExportResult.FAILURE
