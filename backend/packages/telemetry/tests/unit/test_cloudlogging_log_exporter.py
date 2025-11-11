"""Tests for Cloud Logging log exporter - writes OpenTelemetry log records to Google Cloud Logging."""

import logging
import threading
from unittest.mock import Mock, patch

import pytest
from opentelemetry._logs import SeverityNumber
from opentelemetry.sdk._logs import LogData, LogRecord
from opentelemetry.sdk._logs.export import LogExportResult
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.util.instrumentation import InstrumentationScope


@pytest.fixture
def mock_cloud_logging_client():
    """Create a mock Cloud Logging client for testing."""
    with patch("google.cloud.logging.Client") as mock_client_class:
        mock_client = Mock()
        mock_logger = Mock()
        mock_client.logger.return_value = mock_logger
        mock_client_class.return_value = mock_client
        yield mock_client_class, mock_client, mock_logger


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
        severity_number=SeverityNumber.INFO,
        body="Test log message",
        resource=resource,
        attributes={"key": "value", "user.id": "user-123"},
    )

    return LogData(log_record=log_record, instrumentation_scope=scope)


@pytest.fixture
def log_record_without_trace():
    """Create log record without trace context for testing."""
    resource = Resource.create({"service.name": "test"})
    scope = InstrumentationScope("test.logger")
    log_record = LogRecord(
        timestamp=1234567890000000000,
        observed_timestamp=1234567890000000000,
        trace_id=0,
        span_id=0,
        trace_flags=0,
        severity_text="INFO",
        severity_number=SeverityNumber.INFO,
        body="No trace context",
        resource=resource,
        attributes={},
    )
    return LogData(log_record=log_record, instrumentation_scope=scope)


class TestCloudLoggingLogExporterInitialization:
    """Tests for CloudLoggingLogExporter initialization."""

    def test_initializes_with_project_id(self, mock_cloud_logging_client):
        """Test that exporter can be initialized with a project id."""
        from telemetry.config.cloudlogging_log_exporter import CloudLoggingLogExporter

        exporter = CloudLoggingLogExporter(project_id="test-project-123")

        assert exporter is not None

    def test_raises_error_for_empty_project_id(self, mock_cloud_logging_client):
        """Test that empty project_id raises ValueError."""
        from telemetry.config.cloudlogging_log_exporter import CloudLoggingLogExporter

        with pytest.raises(ValueError, match="project_id cannot be empty"):
            CloudLoggingLogExporter(project_id="")

    def test_uses_default_environment(self, mock_cloud_logging_client):
        """Test that exporter defaults to 'dev' environment."""
        from telemetry.config.cloudlogging_log_exporter import CloudLoggingLogExporter

        _, mock_client, _ = mock_cloud_logging_client
        CloudLoggingLogExporter(project_id="test-project")

        # Verify logger was created with default log name
        mock_client.logger.assert_called_once_with("clinicraft-dev")

    def test_uses_custom_environment(self, mock_cloud_logging_client):
        """Test that exporter uses custom environment for log name."""
        from telemetry.config.cloudlogging_log_exporter import CloudLoggingLogExporter

        _, mock_client, _ = mock_cloud_logging_client
        CloudLoggingLogExporter(project_id="test-project", environment="staging")

        # Verify logger was created with staging log name
        mock_client.logger.assert_called_once_with("clinicraft-staging")

    def test_uses_custom_log_name(self, mock_cloud_logging_client):
        """Test that exporter uses custom log name if provided."""
        from telemetry.config.cloudlogging_log_exporter import CloudLoggingLogExporter

        _, mock_client, _ = mock_cloud_logging_client
        CloudLoggingLogExporter(project_id="test-project", environment="dev", log_name="custom-log")

        # Verify logger was created with custom log name
        mock_client.logger.assert_called_once_with("custom-log")

    def test_initializes_cloud_logging_client(self, mock_cloud_logging_client):
        """Test that Cloud Logging client is initialized with project id."""
        from telemetry.config.cloudlogging_log_exporter import CloudLoggingLogExporter

        mock_client_class, _, _ = mock_cloud_logging_client
        CloudLoggingLogExporter(project_id="my-gcp-project")

        # Verify Client was initialized with correct project
        mock_client_class.assert_called_once_with(project="my-gcp-project")


class TestCloudLoggingLogExporterSeverityMapping:
    """Tests for OpenTelemetry severity to Cloud Logging severity mapping."""

    @pytest.mark.parametrize(
        ("otel_severity", "expected_cloud_severity"),
        [
            (SeverityNumber.TRACE, "DEBUG"),
            (SeverityNumber.TRACE2, "DEBUG"),
            (SeverityNumber.TRACE3, "DEBUG"),
            (SeverityNumber.TRACE4, "DEBUG"),
            (SeverityNumber.DEBUG, "DEBUG"),
            (SeverityNumber.DEBUG2, "DEBUG"),
            (SeverityNumber.DEBUG3, "DEBUG"),
            (SeverityNumber.DEBUG4, "DEBUG"),
            (SeverityNumber.INFO, "INFO"),
            (SeverityNumber.INFO2, "INFO"),
            (SeverityNumber.INFO3, "INFO"),
            (SeverityNumber.INFO4, "INFO"),
            (SeverityNumber.WARN, "WARNING"),
            (SeverityNumber.WARN2, "WARNING"),
            (SeverityNumber.WARN3, "WARNING"),
            (SeverityNumber.WARN4, "WARNING"),
            (SeverityNumber.ERROR, "ERROR"),
            (SeverityNumber.ERROR2, "ERROR"),
            (SeverityNumber.ERROR3, "ERROR"),
            (SeverityNumber.ERROR4, "ERROR"),
            (SeverityNumber.FATAL, "CRITICAL"),
            (SeverityNumber.FATAL2, "CRITICAL"),
            (SeverityNumber.FATAL3, "CRITICAL"),
            (SeverityNumber.FATAL4, "CRITICAL"),
        ],
    )
    def test_maps_otel_severity_to_cloud_logging(
        self, otel_severity, expected_cloud_severity, mock_cloud_logging_client
    ):
        """Test that OpenTelemetry severity numbers map correctly to Cloud Logging severities."""
        from telemetry.config.cloudlogging_log_exporter import CloudLoggingLogExporter

        _, _, mock_logger = mock_cloud_logging_client
        exporter = CloudLoggingLogExporter(project_id="test-project")

        # Create log record with specific severity
        resource = Resource.create({"service.name": "test"})
        scope = InstrumentationScope("test.logger")
        log_record = LogRecord(
            timestamp=1234567890000000000,
            observed_timestamp=1234567890000000000,
            trace_id=0,
            span_id=0,
            trace_flags=0,
            severity_text="TEST",
            severity_number=otel_severity,
            body="Test message",
            resource=resource,
            attributes={},
        )
        log_data = LogData(log_record=log_record, instrumentation_scope=scope)

        result = exporter.export([log_data])

        assert result == LogExportResult.SUCCESS
        # Verify Cloud Logging was called with correct severity
        mock_logger.log_struct.assert_called_once()
        call_kwargs = mock_logger.log_struct.call_args[1]
        assert call_kwargs["severity"] == expected_cloud_severity

    def test_handles_invalid_severity_below_range(self, mock_cloud_logging_client):
        """Test that severity values below valid range (< 1) default to INFO."""
        from telemetry.config.cloudlogging_log_exporter import CloudLoggingLogExporter

        _, _, mock_logger = mock_cloud_logging_client
        exporter = CloudLoggingLogExporter(project_id="test-project")

        # Create log record with invalid severity (< 1)
        resource = Resource.create({"service.name": "test"})
        scope = InstrumentationScope("test.logger")
        log_record = LogRecord(
            timestamp=1234567890000000000,
            observed_timestamp=1234567890000000000,
            trace_id=0,
            span_id=0,
            trace_flags=0,
            severity_text="INVALID",
            severity_number=0,  # Invalid: below minimum
            body="Test message",
            resource=resource,
            attributes={},
        )
        log_data = LogData(log_record=log_record, instrumentation_scope=scope)

        result = exporter.export([log_data])

        assert result == LogExportResult.SUCCESS
        # Verify defaults to INFO severity
        call_kwargs = mock_logger.log_struct.call_args[1]
        assert call_kwargs["severity"] == "INFO"

    def test_handles_invalid_severity_above_range(self, mock_cloud_logging_client):
        """Test that severity values above valid range (> 24) cap at CRITICAL."""
        from telemetry.config.cloudlogging_log_exporter import CloudLoggingLogExporter

        _, _, mock_logger = mock_cloud_logging_client
        exporter = CloudLoggingLogExporter(project_id="test-project")

        # Create log record with invalid severity (> 24)
        resource = Resource.create({"service.name": "test"})
        scope = InstrumentationScope("test.logger")
        log_record = LogRecord(
            timestamp=1234567890000000000,
            observed_timestamp=1234567890000000000,
            trace_id=0,
            span_id=0,
            trace_flags=0,
            severity_text="INVALID",
            severity_number=999,  # Invalid: above maximum
            body="Test message",
            resource=resource,
            attributes={},
        )
        log_data = LogData(log_record=log_record, instrumentation_scope=scope)

        result = exporter.export([log_data])

        assert result == LogExportResult.SUCCESS
        # Verify caps at CRITICAL severity
        call_kwargs = mock_logger.log_struct.call_args[1]
        assert call_kwargs["severity"] == "CRITICAL"


class TestCloudLoggingLogExporterExport:
    """Tests for CloudLoggingLogExporter export functionality."""

    def test_exports_single_log_record(self, sample_log_record, mock_cloud_logging_client):
        """Test that exporter writes a single log record to Cloud Logging."""
        from telemetry.config.cloudlogging_log_exporter import CloudLoggingLogExporter

        _, _, mock_logger = mock_cloud_logging_client
        exporter = CloudLoggingLogExporter(project_id="test-project")

        result = exporter.export([sample_log_record])

        assert result == LogExportResult.SUCCESS
        # Verify Cloud Logging was called once
        mock_logger.log_struct.assert_called_once()

    def test_exports_log_record_with_correct_payload(
        self, sample_log_record, mock_cloud_logging_client
    ):
        """Test that log record payload includes all necessary fields."""
        from telemetry.config.cloudlogging_log_exporter import CloudLoggingLogExporter

        _, _, mock_logger = mock_cloud_logging_client
        exporter = CloudLoggingLogExporter(project_id="test-project", environment="dev")

        result = exporter.export([sample_log_record])

        assert result == LogExportResult.SUCCESS
        # Get the payload argument from the call
        call_args = mock_logger.log_struct.call_args
        payload = call_args[0][0]

        # Verify payload structure
        assert payload["message"] == "Test log message"
        assert payload["trace_id"] == "12345678901234567890123456789012"
        assert payload["span_id"] == "1234567890123456"
        assert payload["source"] == "backend"
        assert payload["environment"] == "dev"
        assert payload["key"] == "value"
        assert payload["user.id"] == "user-123"

    def test_exports_log_record_with_trace_correlation(
        self, sample_log_record, mock_cloud_logging_client
    ):
        """Test that log record includes proper Cloud Logging trace format."""
        from telemetry.config.cloudlogging_log_exporter import CloudLoggingLogExporter

        _, _, mock_logger = mock_cloud_logging_client
        exporter = CloudLoggingLogExporter(project_id="my-project")

        result = exporter.export([sample_log_record])

        assert result == LogExportResult.SUCCESS
        # Verify trace and span_id were passed correctly
        call_kwargs = mock_logger.log_struct.call_args[1]
        assert call_kwargs["trace"] == "projects/my-project/traces/12345678901234567890123456789012"
        assert call_kwargs["span_id"] == "1234567890123456"

    def test_exports_log_record_without_trace_context(
        self, log_record_without_trace, mock_cloud_logging_client
    ):
        """Test that log record without trace context is handled correctly."""
        from telemetry.config.cloudlogging_log_exporter import CloudLoggingLogExporter

        _, _, mock_logger = mock_cloud_logging_client
        exporter = CloudLoggingLogExporter(project_id="test-project")

        result = exporter.export([log_record_without_trace])

        assert result == LogExportResult.SUCCESS
        # Verify trace is None when no trace context
        call_kwargs = mock_logger.log_struct.call_args[1]
        assert call_kwargs["trace"] is None
        assert call_kwargs["span_id"] is None

    def test_exports_multiple_log_records(self, mock_cloud_logging_client):
        """Test that exporter writes multiple log records in batch."""
        from telemetry.config.cloudlogging_log_exporter import CloudLoggingLogExporter

        _, _, mock_logger = mock_cloud_logging_client
        exporter = CloudLoggingLogExporter(project_id="test-project")

        # Create multiple log records
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
                severity_number=SeverityNumber.INFO,
                body=f"Log message {i}",
                resource=resource,
                attributes={"index": i},
            )
            log_data = LogData(log_record=log_record, instrumentation_scope=scope)
            log_data_list.append(log_data)

        result = exporter.export(log_data_list)

        assert result == LogExportResult.SUCCESS
        # Verify Cloud Logging was called 5 times
        assert mock_logger.log_struct.call_count == 5

    def test_exports_empty_batch(self, mock_cloud_logging_client):
        """Test that exporter handles empty batch gracefully."""
        from telemetry.config.cloudlogging_log_exporter import CloudLoggingLogExporter

        _, _, mock_logger = mock_cloud_logging_client
        exporter = CloudLoggingLogExporter(project_id="test-project")

        result = exporter.export([])

        assert result == LogExportResult.SUCCESS
        # Verify Cloud Logging was not called
        mock_logger.log_struct.assert_not_called()


class TestCloudLoggingLogExporterErrorHandling:
    """Tests for CloudLoggingLogExporter error handling and graceful degradation."""

    def test_handles_cloud_logging_api_failure_gracefully(
        self, sample_log_record, mock_cloud_logging_client
    ):
        """Test that API failures are handled gracefully without crashing."""
        from telemetry.config.cloudlogging_log_exporter import CloudLoggingLogExporter

        _, _, mock_logger = mock_cloud_logging_client
        # Simulate API failure
        mock_logger.log_struct.side_effect = Exception("Cloud Logging API error")

        exporter = CloudLoggingLogExporter(project_id="test-project")

        # Should not raise exception, should return FAILURE
        result = exporter.export([sample_log_record])

        assert result == LogExportResult.FAILURE

    def test_logs_warning_on_export_failure(
        self, sample_log_record, mock_cloud_logging_client, caplog
    ):
        """Test that export failures are logged as warnings."""
        from telemetry.config.cloudlogging_log_exporter import CloudLoggingLogExporter

        _, _, mock_logger = mock_cloud_logging_client
        mock_logger.log_struct.side_effect = Exception("API error")

        exporter = CloudLoggingLogExporter(project_id="test-project")

        with caplog.at_level(logging.WARNING):
            result = exporter.export([sample_log_record])

        assert result == LogExportResult.FAILURE
        # Verify warning was logged
        assert any(
            "Failed to export logs to Cloud Logging" in record.message for record in caplog.records
        )


class TestCloudLoggingLogExporterThreadSafety:
    """Tests for thread-safety of CloudLoggingLogExporter."""

    def test_concurrent_exports_are_thread_safe(self, mock_cloud_logging_client):
        """Test that concurrent exports don't cause API errors or data corruption."""
        from telemetry.config.cloudlogging_log_exporter import CloudLoggingLogExporter

        _, _, mock_logger = mock_cloud_logging_client
        exporter = CloudLoggingLogExporter(project_id="test-project")

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
                    severity_number=SeverityNumber.INFO,
                    body=f"Thread {thread_id} message {i}",
                    resource=resource,
                    attributes={"thread": thread_id},
                )
                log_data = LogData(log_record=log_record, instrumentation_scope=scope)
                result = exporter.export([log_data])
                assert result == LogExportResult.SUCCESS

        # Create multiple threads writing concurrently
        threads = []
        for tid in range(5):
            thread = threading.Thread(target=export_logs, args=(tid, 10))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Verify all 50 calls succeeded (5 threads x 10 messages)
        assert mock_logger.log_struct.call_count == 50


class TestCloudLoggingLogExporterShutdown:
    """Tests for CloudLoggingLogExporter shutdown behavior."""

    def test_shutdown_sets_shutdown_flag(self, mock_cloud_logging_client):
        """Test that shutdown sets internal shutdown flag."""
        from telemetry.config.cloudlogging_log_exporter import CloudLoggingLogExporter

        exporter = CloudLoggingLogExporter(project_id="test-project")

        exporter.shutdown()

        # Shutdown flag should be set (tested indirectly via export)
        assert exporter._shutdown is True

    def test_exports_after_shutdown_fail_gracefully(
        self, sample_log_record, mock_cloud_logging_client
    ):
        """Test that exports after shutdown return failure status."""
        from telemetry.config.cloudlogging_log_exporter import CloudLoggingLogExporter

        _, _, mock_logger = mock_cloud_logging_client
        exporter = CloudLoggingLogExporter(project_id="test-project")
        exporter.shutdown()

        result = exporter.export([sample_log_record])

        assert result == LogExportResult.FAILURE
        # Verify Cloud Logging was not called
        mock_logger.log_struct.assert_not_called()

    def test_force_flush_returns_true(self, mock_cloud_logging_client):
        """Test that force_flush returns True for active exporter."""
        from telemetry.config.cloudlogging_log_exporter import CloudLoggingLogExporter

        exporter = CloudLoggingLogExporter(project_id="test-project")

        result = exporter.force_flush(timeout_millis=5000)

        assert result is True

    def test_force_flush_returns_false_after_shutdown(self, mock_cloud_logging_client):
        """Test that force_flush returns False after shutdown."""
        from telemetry.config.cloudlogging_log_exporter import CloudLoggingLogExporter

        exporter = CloudLoggingLogExporter(project_id="test-project")
        exporter.shutdown()

        result = exporter.force_flush(timeout_millis=5000)

        assert result is False
