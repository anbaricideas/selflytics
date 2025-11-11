"""Tests for Cloud Logging span exporter - writes OpenTelemetry spans to Google Cloud Logging."""

import logging
import threading
from unittest.mock import Mock, patch

import pytest
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SpanExportResult
from opentelemetry.trace import SpanKind, Status, StatusCode


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
        span.set_status(Status(StatusCode.OK))
        # Span will be readable after context exits

    # Get the completed span (it's now a ReadableSpan)
    return span


class TestCloudLoggingSpanExporterInitialization:
    """Tests for CloudLoggingSpanExporter initialization."""

    def test_initializes_with_project_id(self, mock_cloud_logging_client):
        """Test that exporter can be initialized with a project id."""
        from telemetry.config.cloudlogging_exporter import CloudLoggingSpanExporter

        exporter = CloudLoggingSpanExporter(project_id="test-project-123")

        assert exporter is not None

    def test_raises_error_for_empty_project_id(self, mock_cloud_logging_client):
        """Test that empty project_id raises ValueError."""
        from telemetry.config.cloudlogging_exporter import CloudLoggingSpanExporter

        with pytest.raises(ValueError, match="project_id cannot be empty"):
            CloudLoggingSpanExporter(project_id="")

    def test_uses_default_environment(self, mock_cloud_logging_client):
        """Test that exporter defaults to 'dev' environment."""
        from telemetry.config.cloudlogging_exporter import CloudLoggingSpanExporter

        _, mock_client, _ = mock_cloud_logging_client
        _exporter = CloudLoggingSpanExporter(project_id="test-project")

        # Verify logger was created with default log name
        mock_client.logger.assert_called_once_with("clinicraft-dev")

    def test_uses_custom_environment(self, mock_cloud_logging_client):
        """Test that exporter uses custom environment for log name."""
        from telemetry.config.cloudlogging_exporter import CloudLoggingSpanExporter

        _, mock_client, _ = mock_cloud_logging_client
        _exporter = CloudLoggingSpanExporter(project_id="test-project", environment="staging")

        # Verify logger was created with staging log name
        mock_client.logger.assert_called_once_with("clinicraft-staging")

    def test_uses_custom_log_name(self, mock_cloud_logging_client):
        """Test that exporter uses custom log name if provided."""
        from telemetry.config.cloudlogging_exporter import CloudLoggingSpanExporter

        _, mock_client, _ = mock_cloud_logging_client
        _exporter = CloudLoggingSpanExporter(
            project_id="test-project", environment="dev", log_name="custom-log"
        )

        # Verify logger was created with custom log name
        mock_client.logger.assert_called_once_with("custom-log")

    def test_initializes_cloud_logging_client(self, mock_cloud_logging_client):
        """Test that Cloud Logging client is initialized with project id."""
        from telemetry.config.cloudlogging_exporter import CloudLoggingSpanExporter

        mock_client_class, _, _ = mock_cloud_logging_client
        _exporter = CloudLoggingSpanExporter(project_id="my-gcp-project")

        # Verify Client was initialized with correct project
        mock_client_class.assert_called_once_with(project="my-gcp-project")


class TestCloudLoggingSpanExporterExport:
    """Tests for CloudLoggingSpanExporter export functionality."""

    def test_exports_single_span(self, sample_span, mock_cloud_logging_client):
        """Test that exporter writes a single span to Cloud Logging."""
        from telemetry.config.cloudlogging_exporter import CloudLoggingSpanExporter

        _, _, mock_logger = mock_cloud_logging_client
        exporter = CloudLoggingSpanExporter(project_id="test-project")

        result = exporter.export([sample_span])

        assert result == SpanExportResult.SUCCESS
        # Verify Cloud Logging was called once
        mock_logger.log_struct.assert_called_once()

    def test_exports_span_with_correct_payload(self, sample_span, mock_cloud_logging_client):
        """Test that span payload includes all necessary fields."""
        from telemetry.config.cloudlogging_exporter import CloudLoggingSpanExporter

        _, _, mock_logger = mock_cloud_logging_client
        exporter = CloudLoggingSpanExporter(project_id="test-project", environment="dev")

        result = exporter.export([sample_span])

        assert result == SpanExportResult.SUCCESS
        # Get the payload argument from the call
        call_args = mock_logger.log_struct.call_args
        payload = call_args[0][0]

        # Verify payload structure
        assert payload["span_name"] == "test_operation"
        assert "trace_id" in payload
        assert "span_id" in payload
        assert payload["source"] == "backend"
        assert payload["environment"] == "dev"
        assert payload["kind"] == "INTERNAL"
        assert payload["status"] == "OK"
        assert "start_time" in payload
        assert "end_time" in payload
        assert "duration_ns" in payload
        assert isinstance(payload["attributes"], dict)
        assert payload["attributes"]["http.method"] == "GET"

    def test_exports_span_with_trace_correlation(self, sample_span, mock_cloud_logging_client):
        """Test that span includes proper Cloud Logging trace format."""
        from telemetry.config.cloudlogging_exporter import CloudLoggingSpanExporter

        _, _, mock_logger = mock_cloud_logging_client
        exporter = CloudLoggingSpanExporter(project_id="my-project")

        result = exporter.export([sample_span])

        assert result == SpanExportResult.SUCCESS
        # Verify trace and span_id were passed correctly
        call_kwargs = mock_logger.log_struct.call_args[1]
        trace_id = format(sample_span.context.trace_id, "032x")
        span_id = format(sample_span.context.span_id, "016x")
        assert call_kwargs["trace"] == f"projects/my-project/traces/{trace_id}"
        assert call_kwargs["span_id"] == span_id

    def test_exports_span_with_parent_span_id(self, mock_cloud_logging_client):
        """Test that span with parent includes parent_span_id in payload."""
        from telemetry.config.cloudlogging_exporter import CloudLoggingSpanExporter

        _, _, mock_logger = mock_cloud_logging_client
        exporter = CloudLoggingSpanExporter(project_id="test-project")

        # Create parent and child spans
        resource = Resource.create({"service.name": "test"})
        tracer_provider = TracerProvider(resource=resource)
        tracer = tracer_provider.get_tracer("test.tracer")

        with tracer.start_as_current_span("parent_span") as parent_span:
            parent_span_id = format(parent_span.get_span_context().span_id, "016x")
            with tracer.start_as_current_span("child_span") as child_span:
                pass  # Child span completes

        result = exporter.export([child_span])

        assert result == SpanExportResult.SUCCESS
        # Verify parent_span_id is in payload
        call_args = mock_logger.log_struct.call_args
        payload = call_args[0][0]
        assert payload["parent_span_id"] == parent_span_id

    def test_exports_span_without_parent(self, sample_span, mock_cloud_logging_client):
        """Test that root span (no parent) has None parent_span_id."""
        from telemetry.config.cloudlogging_exporter import CloudLoggingSpanExporter

        _, _, mock_logger = mock_cloud_logging_client
        exporter = CloudLoggingSpanExporter(project_id="test-project")

        result = exporter.export([sample_span])

        assert result == SpanExportResult.SUCCESS
        # Verify parent_span_id is None for root span
        call_args = mock_logger.log_struct.call_args
        payload = call_args[0][0]
        assert payload["parent_span_id"] is None

    def test_exports_multiple_spans(self, mock_cloud_logging_client):
        """Test that exporter writes multiple spans in batch."""
        from telemetry.config.cloudlogging_exporter import CloudLoggingSpanExporter

        _, _, mock_logger = mock_cloud_logging_client
        exporter = CloudLoggingSpanExporter(project_id="test-project")

        # Create multiple spans
        resource = Resource.create({"service.name": "test"})
        tracer_provider = TracerProvider(resource=resource)
        tracer = tracer_provider.get_tracer("test.tracer")
        spans = []

        for i in range(5):
            with tracer.start_as_current_span(f"operation_{i}") as span:
                pass
            spans.append(span)

        result = exporter.export(spans)

        assert result == SpanExportResult.SUCCESS
        # Verify Cloud Logging was called 5 times
        assert mock_logger.log_struct.call_count == 5

    def test_exports_empty_batch(self, mock_cloud_logging_client):
        """Test that exporter handles empty batch gracefully."""
        from telemetry.config.cloudlogging_exporter import CloudLoggingSpanExporter

        _, _, mock_logger = mock_cloud_logging_client
        exporter = CloudLoggingSpanExporter(project_id="test-project")

        result = exporter.export([])

        assert result == SpanExportResult.SUCCESS
        # Verify Cloud Logging was not called
        mock_logger.log_struct.assert_not_called()

    @pytest.mark.parametrize(
        ("span_kind", "expected_kind_str"),
        [
            (SpanKind.INTERNAL, "INTERNAL"),
            (SpanKind.SERVER, "SERVER"),
            (SpanKind.CLIENT, "CLIENT"),
            (SpanKind.PRODUCER, "PRODUCER"),
            (SpanKind.CONSUMER, "CONSUMER"),
        ],
    )
    def test_exports_span_kind_correctly(
        self, span_kind, expected_kind_str, mock_cloud_logging_client
    ):
        """Test that different span kinds are exported correctly."""
        from telemetry.config.cloudlogging_exporter import CloudLoggingSpanExporter

        _, _, mock_logger = mock_cloud_logging_client
        exporter = CloudLoggingSpanExporter(project_id="test-project")

        # Create span with specific kind
        resource = Resource.create({"service.name": "test"})
        tracer_provider = TracerProvider(resource=resource)
        tracer = tracer_provider.get_tracer("test.tracer")

        with tracer.start_as_current_span("test_span", kind=span_kind) as span:
            pass

        result = exporter.export([span])

        assert result == SpanExportResult.SUCCESS
        # Verify kind is in payload
        call_args = mock_logger.log_struct.call_args
        payload = call_args[0][0]
        assert payload["kind"] == expected_kind_str

    @pytest.mark.parametrize(
        ("status_code", "expected_status_str"),
        [
            (StatusCode.UNSET, "UNSET"),
            (StatusCode.OK, "OK"),
            (StatusCode.ERROR, "ERROR"),
        ],
    )
    def test_exports_span_status_correctly(
        self, status_code, expected_status_str, mock_cloud_logging_client
    ):
        """Test that different span statuses are exported correctly."""
        from telemetry.config.cloudlogging_exporter import CloudLoggingSpanExporter

        _, _, mock_logger = mock_cloud_logging_client
        exporter = CloudLoggingSpanExporter(project_id="test-project")

        # Create span with specific status
        resource = Resource.create({"service.name": "test"})
        tracer_provider = TracerProvider(resource=resource)
        tracer = tracer_provider.get_tracer("test.tracer")

        with tracer.start_as_current_span("test_span") as span:
            span.set_status(Status(status_code))

        result = exporter.export([span])

        assert result == SpanExportResult.SUCCESS
        # Verify status is in payload
        call_args = mock_logger.log_struct.call_args
        payload = call_args[0][0]
        assert payload["status"] == expected_status_str


class TestCloudLoggingSpanExporterErrorHandling:
    """Tests for CloudLoggingSpanExporter error handling and graceful degradation."""

    def test_handles_cloud_logging_api_failure_gracefully(
        self, sample_span, mock_cloud_logging_client
    ):
        """Test that API failures are handled gracefully without crashing."""
        from telemetry.config.cloudlogging_exporter import CloudLoggingSpanExporter

        _, _, mock_logger = mock_cloud_logging_client
        # Simulate API failure
        mock_logger.log_struct.side_effect = Exception("Cloud Logging API error")

        exporter = CloudLoggingSpanExporter(project_id="test-project")

        # Should not raise exception, should return FAILURE
        result = exporter.export([sample_span])

        assert result == SpanExportResult.FAILURE

    def test_logs_warning_on_export_failure(self, sample_span, mock_cloud_logging_client, caplog):
        """Test that export failures are logged as warnings."""
        from telemetry.config.cloudlogging_exporter import CloudLoggingSpanExporter

        _, _, mock_logger = mock_cloud_logging_client
        mock_logger.log_struct.side_effect = Exception("API error")

        exporter = CloudLoggingSpanExporter(project_id="test-project")

        with caplog.at_level(logging.WARNING):
            result = exporter.export([sample_span])

        assert result == SpanExportResult.FAILURE
        # Verify warning was logged
        assert any(
            "Failed to export spans to Cloud Logging" in record.message for record in caplog.records
        )


class TestCloudLoggingSpanExporterThreadSafety:
    """Tests for thread-safety of CloudLoggingSpanExporter."""

    def test_concurrent_exports_are_thread_safe(self, mock_cloud_logging_client):
        """Test that concurrent exports don't cause API errors or data corruption."""
        from telemetry.config.cloudlogging_exporter import CloudLoggingSpanExporter

        _, _, mock_logger = mock_cloud_logging_client
        exporter = CloudLoggingSpanExporter(project_id="test-project")

        resource = Resource.create({"service.name": "test"})
        tracer_provider = TracerProvider(resource=resource)
        tracer = tracer_provider.get_tracer("test.tracer")

        def export_spans(thread_id: int, count: int):
            for i in range(count):
                with tracer.start_as_current_span(f"thread_{thread_id}_span_{i}") as span:
                    span.set_attribute("thread", thread_id)

                result = exporter.export([span])
                assert result == SpanExportResult.SUCCESS

        # Create multiple threads writing concurrently
        threads = []
        for tid in range(5):
            thread = threading.Thread(target=export_spans, args=(tid, 10))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Verify all 50 calls succeeded (5 threads x 10 spans)
        assert mock_logger.log_struct.call_count == 50


class TestCloudLoggingSpanExporterShutdown:
    """Tests for CloudLoggingSpanExporter shutdown behavior."""

    def test_shutdown_sets_shutdown_flag(self, mock_cloud_logging_client):
        """Test that shutdown sets internal shutdown flag."""
        from telemetry.config.cloudlogging_exporter import CloudLoggingSpanExporter

        exporter = CloudLoggingSpanExporter(project_id="test-project")

        exporter.shutdown()

        # Shutdown flag should be set (tested indirectly via export)
        assert exporter._shutdown is True

    def test_exports_after_shutdown_fail_gracefully(self, sample_span, mock_cloud_logging_client):
        """Test that exports after shutdown return failure status."""
        from telemetry.config.cloudlogging_exporter import CloudLoggingSpanExporter

        _, _, mock_logger = mock_cloud_logging_client
        exporter = CloudLoggingSpanExporter(project_id="test-project")
        exporter.shutdown()

        result = exporter.export([sample_span])

        assert result == SpanExportResult.FAILURE
        # Verify Cloud Logging was not called
        mock_logger.log_struct.assert_not_called()

    def test_force_flush_returns_true(self, mock_cloud_logging_client):
        """Test that force_flush returns True for active exporter."""
        from telemetry.config.cloudlogging_exporter import CloudLoggingSpanExporter

        exporter = CloudLoggingSpanExporter(project_id="test-project")

        result = exporter.force_flush(timeout_millis=5000)

        assert result is True

    def test_force_flush_returns_false_after_shutdown(self, mock_cloud_logging_client):
        """Test that force_flush returns False after shutdown."""
        from telemetry.config.cloudlogging_exporter import CloudLoggingSpanExporter

        exporter = CloudLoggingSpanExporter(project_id="test-project")
        exporter.shutdown()

        result = exporter.force_flush(timeout_millis=5000)

        assert result is False
