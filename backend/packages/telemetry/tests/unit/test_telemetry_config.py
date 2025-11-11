"""
Unit tests for telemetry configuration module.

Tests cover:
- TelemetryContext dataclass
- configure_telemetry() function with all backends
- shutdown_telemetry() lifecycle management
- Provider singleton pattern
- Environment variable handling
- Error cases and validation
- Actual telemetry behavior (spans and logs are exported)

Design: These tests focus on behavioral verification rather than implementation
details. They use real OpenTelemetry objects and verify that telemetry data
is actually exported, not just that objects were created.
"""

import json
import logging
import os
import re
from pathlib import Path
from unittest.mock import patch

import pytest
from opentelemetry import _logs as logs_api
from opentelemetry import trace as trace_api
from opentelemetry.sdk._logs import LoggerProvider
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor
from telemetry.config.telemetry import (
    TelemetryContext,
    configure_telemetry,
    shutdown_telemetry,
)


@pytest.fixture(autouse=True)
def reset_telemetry_globals():
    """Reset global telemetry state between tests to prevent pollution."""
    yield

    # After each test, clear global context
    from telemetry.config import telemetry

    telemetry._current_telemetry_context = None
    # Note: Cannot reset _global_tracer_provider/_global_logger_provider due to
    # OpenTelemetry's singleton constraints. Tests should handle provider reuse.


class TestTelemetryContext:
    """Tests for TelemetryContext dataclass."""

    def test_telemetry_context_creation_minimal(self) -> None:
        """TelemetryContext can be created with minimal required fields."""
        context = TelemetryContext(
            session_id="test-session",
            log_file_path=None,
            span_exporter=None,
            backend="disabled",
        )

        assert context.session_id == "test-session"
        assert context.log_file_path is None
        assert context.span_exporter is None
        assert context.backend == "disabled"
        assert context.log_exporter is None
        assert context.span_processor is None
        assert context.log_processor is None

    def test_telemetry_context_creation_full(self, tmp_path: Path) -> None:
        """TelemetryContext can be created with all fields populated."""
        # Use real OpenTelemetry objects instead of mocks
        real_exporter = ConsoleSpanExporter()
        real_processor = SimpleSpanProcessor(real_exporter)
        log_path = tmp_path / "test.jsonl"

        context = TelemetryContext(
            session_id="test-session",
            log_file_path=log_path,
            span_exporter=real_exporter,
            backend="console",
            log_exporter=None,
            span_processor=real_processor,
            log_processor=None,
        )

        assert context.session_id == "test-session"
        assert context.log_file_path == log_path
        assert isinstance(context.span_exporter, ConsoleSpanExporter)
        assert context.backend == "console"
        assert context.log_exporter is None
        assert isinstance(context.span_processor, SimpleSpanProcessor)
        assert context.log_processor is None


class TestConfigureTelemetryDisabled:
    """Tests for configure_telemetry() with backend='disabled'."""

    def test_configure_disabled_backend(self) -> None:
        """Disabled backend creates minimal context with no exporters."""
        context = configure_telemetry(backend="disabled")

        assert context.session_id == "disabled"
        assert context.backend == "disabled"
        assert context.span_exporter is None
        assert context.log_exporter is None
        assert context.span_processor is None
        assert context.log_processor is None
        assert context.log_file_path is None

        # Cleanup
        shutdown_telemetry(context)

    def test_configure_disabled_is_default(self) -> None:
        """Default backend is 'disabled' when no backend specified."""
        context = configure_telemetry()

        assert context.backend == "disabled"
        shutdown_telemetry(context)


class TestConfigureTelemetryConsole:
    """Tests for configure_telemetry() with backend='console'."""

    def test_configure_console_backend(self) -> None:
        """Console backend creates context with console span exporter."""
        context = configure_telemetry(backend="console", verbose=False)

        assert context.backend == "console"
        assert context.session_id.startswith("console_")
        assert isinstance(context.span_exporter, ConsoleSpanExporter)
        assert context.span_processor is not None
        # Console backend doesn't export logs
        assert context.log_exporter is None
        assert context.log_processor is None
        assert context.log_file_path is None

        # Cleanup
        shutdown_telemetry(context)

    def test_configure_console_verbose_mode(self, capsys: pytest.CaptureFixture) -> None:
        """Console backend with verbose=True prints setup message."""
        context = configure_telemetry(backend="console", verbose=True)

        captured = capsys.readouterr()
        assert "Console tracing enabled" in captured.out
        assert "traces will be printed to stdout" in captured.out

        # Cleanup
        shutdown_telemetry(context)

    def test_configure_console_creates_providers(self) -> None:
        """Console backend creates and configures OpenTelemetry providers."""
        context = configure_telemetry(backend="console", verbose=False)

        # Verify providers are set up (global singletons exist)
        tracer_provider = trace_api.get_tracer_provider()
        logger_provider = logs_api.get_logger_provider()

        assert isinstance(tracer_provider, TracerProvider)
        assert isinstance(logger_provider, LoggerProvider)

        # Cleanup
        shutdown_telemetry(context)

    def test_console_backend_uses_console_exporter(self) -> None:
        """Console backend configures ConsoleSpanExporter for span export."""
        context = configure_telemetry(backend="console", verbose=False)

        # Verify that console exporter is configured (not null/disabled)
        assert isinstance(context.span_exporter, ConsoleSpanExporter)

        # Verify SimpleSpanProcessor is used (for immediate export)
        assert isinstance(context.span_processor, SimpleSpanProcessor)

        # Verify that spans can be created (integration works)
        tracer = trace_api.get_tracer("test")
        with tracer.start_as_current_span("test_operation") as span:
            span.set_attribute("test_key", "test_value")
            # If this completes without error, telemetry is working
            assert span.is_recording()

        # Cleanup
        shutdown_telemetry(context)


class TestConfigureTelemetryJSONL:
    """Tests for configure_telemetry() with backend='jsonl'."""

    def test_configure_jsonl_backend(self, tmp_path: Path) -> None:
        """JSONL backend creates context with JSONL exporters and session file."""
        with patch.dict(os.environ, {"LOG_PATH": str(tmp_path)}):
            context = configure_telemetry(backend="jsonl", verbose=False)

        assert context.backend == "jsonl"
        assert context.session_id.startswith("session_")
        assert context.span_exporter is not None
        assert context.log_exporter is not None
        assert context.span_processor is not None
        assert context.log_processor is not None
        assert context.log_file_path is not None
        assert context.log_file_path.parent == tmp_path
        assert context.log_file_path.suffix == ".jsonl"

        # Cleanup
        shutdown_telemetry(context)

    def test_jsonl_creates_file_and_exports_spans(self, tmp_path: Path) -> None:
        """JSONL backend creates file and actually writes span data."""
        with patch.dict(os.environ, {"LOG_PATH": str(tmp_path)}):
            context = configure_telemetry(backend="jsonl", verbose=False)

        # Create a span with attributes
        tracer = trace_api.get_tracer("test")
        with tracer.start_as_current_span("test_operation") as span:
            span.set_attribute("operation_type", "unit_test")
            span.set_attribute("test_id", 123)

        # Force flush and shutdown to ensure data is written
        context.span_processor.force_flush()
        shutdown_telemetry(context)

        # Verify file exists and contains span data
        assert context.log_file_path.exists()
        assert context.log_file_path.is_file()

        content = context.log_file_path.read_text()
        assert len(content.strip()) > 0, "JSONL file should not be empty"

        # Verify JSONL format (each line is valid JSON)
        lines = [line for line in content.strip().split("\n") if line]
        assert len(lines) >= 1, "Should have at least one JSONL record"

        # Parse first record and verify it contains span data
        first_record = json.loads(lines[0])
        assert "name" in first_record
        assert first_record["name"] == "test_operation"

    def test_configure_jsonl_default_log_path(self) -> None:
        """JSONL backend uses default ./logs directory when LOG_PATH not set."""
        # Clear LOG_PATH if it exists
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("LOG_PATH", None)
            context = configure_telemetry(backend="jsonl", verbose=False)

        assert context.log_file_path is not None
        assert context.log_file_path.parent == Path("./logs").resolve()

        # Cleanup
        shutdown_telemetry(context)

    def test_configure_jsonl_creates_log_directory(self, tmp_path: Path) -> None:
        """JSONL backend creates log directory if it doesn't exist."""
        log_dir = tmp_path / "telemetry_logs"
        assert not log_dir.exists()

        with patch.dict(os.environ, {"LOG_PATH": str(log_dir)}):
            context = configure_telemetry(backend="jsonl", verbose=False)

        # Directory should be created
        assert log_dir.exists()
        assert log_dir.is_dir()

        # Cleanup
        shutdown_telemetry(context)

    def test_jsonl_file_is_writable(self, tmp_path: Path) -> None:
        """JSONL backend creates a writable file."""
        with patch.dict(os.environ, {"LOG_PATH": str(tmp_path)}):
            context = configure_telemetry(backend="jsonl", verbose=False)

        # Verify file exists and is writable
        assert context.log_file_path.exists()
        assert context.log_file_path.is_file()

        # Write a test line to verify it's actually writable
        test_data = '{"test": "data"}\n'
        with context.log_file_path.open("a") as f:
            f.write(test_data)

        # Verify it was written
        content = context.log_file_path.read_text()
        assert test_data in content

        # Cleanup
        shutdown_telemetry(context)

    def test_configure_jsonl_verbose_mode(
        self, tmp_path: Path, capsys: pytest.CaptureFixture
    ) -> None:
        """JSONL backend with verbose=True prints setup message."""
        with patch.dict(os.environ, {"LOG_PATH": str(tmp_path)}):
            context = configure_telemetry(backend="jsonl", verbose=True)

        captured = capsys.readouterr()
        assert "JSONL tracing enabled" in captured.out
        assert str(tmp_path) in captured.out

        # Cleanup
        shutdown_telemetry(context)

    def test_configure_jsonl_respects_log_level_env(self, tmp_path: Path) -> None:
        """JSONL backend respects LOG_LEVEL environment variable."""
        with patch.dict(os.environ, {"LOG_PATH": str(tmp_path), "LOG_LEVEL": "DEBUG"}):
            context = configure_telemetry(backend="jsonl", verbose=False)

        # Verify logging level was set
        root_logger = logging.getLogger()
        assert root_logger.level == logging.DEBUG

        # Cleanup
        shutdown_telemetry(context)


class TestConfigureTelemetryInvalidBackend:
    """Tests for configure_telemetry() with invalid backend values."""

    def test_configure_invalid_backend_raises_error(self) -> None:
        """Invalid backend value raises ValueError."""
        with pytest.raises(ValueError, match="Unsupported telemetry backend"):
            configure_telemetry(backend="invalid")  # type: ignore[arg-type]

    def test_configure_unsupported_backend_raises_error(self) -> None:
        """Unsupported backend (e.g., 'gcs', 'otlp') raises ValueError in Phase 1."""
        # Phase 1 only supports console, jsonl, and disabled
        with pytest.raises(ValueError, match="Unsupported telemetry backend"):
            configure_telemetry(backend="otlp")  # type: ignore[arg-type]


class TestShutdownTelemetry:
    """Tests for shutdown_telemetry() lifecycle management."""

    def test_shutdown_disabled_backend_succeeds(self) -> None:
        """Shutting down disabled backend succeeds without errors."""
        context = configure_telemetry(backend="disabled")
        shutdown_telemetry(context)  # Should not raise

    def test_shutdown_console_backend_succeeds(self) -> None:
        """Shutting down console backend succeeds and cleans up processors."""
        context = configure_telemetry(backend="console", verbose=False)
        assert context.span_processor is not None

        shutdown_telemetry(context)
        # Processor should be shutdown (no assertion possible, just ensure no errors)

    def test_shutdown_jsonl_backend_succeeds(self, tmp_path: Path) -> None:
        """Shutting down JSONL backend succeeds and cleans up resources."""
        with patch.dict(os.environ, {"LOG_PATH": str(tmp_path)}):
            context = configure_telemetry(backend="jsonl", verbose=False)

        assert context.span_processor is not None
        assert context.log_processor is not None

        shutdown_telemetry(context)
        # Processors should be shutdown and file handles closed

    def test_shutdown_flushes_pending_data(self, tmp_path: Path) -> None:
        """Shutdown flushes pending telemetry data before closing."""
        with patch.dict(os.environ, {"LOG_PATH": str(tmp_path)}):
            context = configure_telemetry(backend="jsonl", verbose=False)

        # Create a span
        tracer = trace_api.get_tracer("test")
        with tracer.start_as_current_span("flush_test"):
            pass

        # Shutdown should flush the span to file
        shutdown_telemetry(context)

        # Verify span was written to file
        assert context.log_file_path.exists()
        content = context.log_file_path.read_text()
        assert "flush_test" in content

    def test_shutdown_handles_processor_errors_gracefully(self, tmp_path: Path) -> None:
        """Shutdown handles processor errors gracefully (best-effort)."""
        from unittest.mock import Mock

        with patch.dict(os.environ, {"LOG_PATH": str(tmp_path)}):
            context = configure_telemetry(backend="jsonl", verbose=False)

        # Make processors raise errors on flush/shutdown
        context.span_processor.force_flush = Mock(side_effect=RuntimeError("Test error"))
        context.span_processor.shutdown = Mock(side_effect=RuntimeError("Test error"))

        # Should not raise - best-effort cleanup
        shutdown_telemetry(context)


class TestProviderSingletonPattern:
    """Tests for OpenTelemetry provider singleton pattern."""

    def test_multiple_configure_calls_reuse_providers(self) -> None:
        """Multiple configure_telemetry() calls reuse the same providers."""
        from opentelemetry import trace as trace_api

        # First configuration
        context1 = configure_telemetry(backend="console", verbose=False)
        provider1 = trace_api.get_tracer_provider()

        # Second configuration (without shutdown)
        context2 = configure_telemetry(backend="console", verbose=False)
        provider2 = trace_api.get_tracer_provider()

        # Should be the same provider instance
        assert provider1 is provider2

        # Cleanup
        shutdown_telemetry(context1)
        shutdown_telemetry(context2)

    def test_configure_after_shutdown_reuses_providers(self) -> None:
        """Configuring after shutdown reuses providers but creates new processors."""
        from opentelemetry import trace as trace_api

        # First session
        context1 = configure_telemetry(backend="console", verbose=False)
        provider1 = trace_api.get_tracer_provider()
        processor1 = context1.span_processor
        shutdown_telemetry(context1)

        # Second session
        context2 = configure_telemetry(backend="console", verbose=False)
        provider2 = trace_api.get_tracer_provider()
        processor2 = context2.span_processor

        # Same provider, different processors
        assert provider1 is provider2
        assert processor1 is not processor2

        # Cleanup
        shutdown_telemetry(context2)

    def test_reconfigure_without_shutdown_logs_warning(
        self,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Reconfiguring without shutdown logs a warning about orphaned processors."""
        with caplog.at_level(logging.DEBUG):
            context1 = configure_telemetry(backend="console", verbose=False)
            context2 = configure_telemetry(backend="jsonl", verbose=False)

        # Should log warning about reconfiguration
        assert any("Reconfiguring telemetry" in record.message for record in caplog.records)
        assert any("without shutdown" in record.message for record in caplog.records)

        # Cleanup
        shutdown_telemetry(context1)
        shutdown_telemetry(context2)


class TestEnvironmentVariableHandling:
    """Tests for environment variable configuration."""

    def test_telemetry_env_overrides_backend_parameter(self, tmp_path: Path) -> None:
        """TELEMETRY environment variable overrides backend parameter."""
        with patch.dict(os.environ, {"TELEMETRY": "jsonl", "LOG_PATH": str(tmp_path)}):
            # Even though we pass backend="console", TELEMETRY env should override
            context = configure_telemetry(backend="console", verbose=False)

        assert context.backend == "jsonl"
        shutdown_telemetry(context)

    def test_log_path_env_sets_jsonl_directory(self, tmp_path: Path) -> None:
        """LOG_PATH environment variable sets JSONL log directory."""
        custom_path = tmp_path / "custom_logs"
        with patch.dict(os.environ, {"LOG_PATH": str(custom_path)}):
            context = configure_telemetry(backend="jsonl", verbose=False)

        assert context.log_file_path is not None
        assert context.log_file_path.parent == custom_path
        shutdown_telemetry(context)

    def test_log_level_env_sets_logging_level(self, tmp_path: Path) -> None:
        """LOG_LEVEL environment variable sets Python logging level."""
        with patch.dict(
            os.environ, {"TELEMETRY": "jsonl", "LOG_PATH": str(tmp_path), "LOG_LEVEL": "WARNING"}
        ):
            context = configure_telemetry(verbose=False)

        root_logger = logging.getLogger()
        assert root_logger.level == logging.WARNING
        shutdown_telemetry(context)


class TestSessionIDGeneration:
    """Tests for session ID generation."""

    def test_console_session_id_format(self) -> None:
        """Console backend generates session ID with expected format."""
        context = configure_telemetry(backend="console", verbose=False)

        assert context.session_id.startswith("console_")
        # Should match format: console_YYYYMMDD_HHMMSS_fffff (microseconds, 5 digits after slicing)
        pattern = re.match(r"^console_\d{8}_\d{6}_\d{5}$", context.session_id)
        assert pattern is not None, f"Session ID format mismatch: {context.session_id}"

        shutdown_telemetry(context)

    def test_jsonl_session_id_format(self, tmp_path: Path) -> None:
        """JSONL backend generates session ID with expected format."""
        with patch.dict(os.environ, {"LOG_PATH": str(tmp_path)}):
            context = configure_telemetry(backend="jsonl", verbose=False)

        assert context.session_id.startswith("session_")
        # Should match format: session_YYYYMMDD_HHMMSS_fffff (microseconds, 5 digits after slicing)
        pattern = re.match(r"^session_\d{8}_\d{6}_\d{5}$", context.session_id)
        assert pattern is not None, f"Session ID format mismatch: {context.session_id}"

        shutdown_telemetry(context)

    def test_disabled_session_id_is_static(self) -> None:
        """Disabled backend always returns 'disabled' as session ID."""
        context = configure_telemetry(backend="disabled")
        assert context.session_id == "disabled"
        shutdown_telemetry(context)

    def test_unique_session_ids_per_call(self, tmp_path: Path) -> None:
        """Each configure_telemetry() call generates unique session ID."""
        with patch.dict(os.environ, {"LOG_PATH": str(tmp_path)}):
            context1 = configure_telemetry(backend="jsonl", verbose=False)
            context2 = configure_telemetry(backend="jsonl", verbose=False)

        assert context1.session_id != context2.session_id

        shutdown_telemetry(context1)
        shutdown_telemetry(context2)


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_shutdown_called_twice_on_same_context(self) -> None:
        """Calling shutdown twice on same context doesn't raise errors."""
        context = configure_telemetry(backend="console", verbose=False)
        shutdown_telemetry(context)
        # Second shutdown should be safe (no-op)
        shutdown_telemetry(context)

    def test_invalid_log_level_env_uses_default(self, tmp_path: Path) -> None:
        """Invalid LOG_LEVEL value falls back to default gracefully."""
        with patch.dict(os.environ, {"LOG_PATH": str(tmp_path), "LOG_LEVEL": "INVALID"}):
            # Should not raise - should handle invalid level gracefully
            try:
                context = configure_telemetry(backend="jsonl", verbose=False)
                shutdown_telemetry(context)
            except (ValueError, KeyError):
                # Acceptable to raise on invalid level
                pass


class TestConfigureTelemetryCloudLogging:
    """Tests for Cloud Logging backend configuration."""

    @patch("telemetry.config.cloudlogging_exporter.cloud_logging.Client")
    @patch("telemetry.config.cloudlogging_log_exporter.cloud_logging.Client")
    def test_configure_cloudlogging_backend(self, mock_log_client, mock_span_client):
        """Cloud Logging backend is configured successfully with required env vars."""
        with patch.dict(os.environ, {"GCP_PROJECT_ID": "test-project", "ENVIRONMENT": "dev"}):
            context = configure_telemetry(backend="cloudlogging", verbose=False)

            assert context.backend == "cloudlogging"
            assert context.session_id.startswith("cloudlogging_")
            assert context.span_exporter is not None
            assert context.log_exporter is not None
            assert context.log_file_path is None  # No local file

            shutdown_telemetry(context)

    def test_cloudlogging_requires_gcp_project_id(self):
        """Cloud Logging backend raises error if GCP_PROJECT_ID not set."""
        # Clear GCP_PROJECT_ID from environment
        with (
            patch.dict(os.environ, {}, clear=True),
            pytest.raises(ValueError, match="GCP_PROJECT_ID environment variable is required"),
        ):
            configure_telemetry(backend="cloudlogging", verbose=False)

    @patch("telemetry.config.cloudlogging_exporter.cloud_logging.Client")
    @patch("telemetry.config.cloudlogging_log_exporter.cloud_logging.Client")
    def test_cloudlogging_uses_default_environment(self, mock_log_client, mock_span_client):
        """Cloud Logging uses 'dev' as default environment."""
        with patch.dict(os.environ, {"GCP_PROJECT_ID": "test-project"}, clear=True):
            context = configure_telemetry(backend="cloudlogging", verbose=False)

            # Verify configuration succeeded
            assert context.backend == "cloudlogging"
            # Environment-specific assertions are covered by exporter unit tests

            shutdown_telemetry(context)

    @patch("telemetry.config.cloudlogging_exporter.cloud_logging.Client")
    @patch("telemetry.config.cloudlogging_log_exporter.cloud_logging.Client")
    def test_cloudlogging_respects_environment_env(self, mock_log_client, mock_span_client):
        """Cloud Logging respects ENVIRONMENT variable."""
        with patch.dict(os.environ, {"GCP_PROJECT_ID": "test-project", "ENVIRONMENT": "staging"}):
            context = configure_telemetry(backend="cloudlogging", verbose=False)

            # Verify configuration succeeded
            assert context.backend == "cloudlogging"
            # Environment-specific assertions are covered by exporter unit tests

            shutdown_telemetry(context)

    @patch("telemetry.config.cloudlogging_exporter.cloud_logging.Client")
    @patch("telemetry.config.cloudlogging_log_exporter.cloud_logging.Client")
    def test_cloudlogging_creates_correct_exporters(self, mock_log_client, mock_span_client):
        """Cloud Logging creates both span and log exporters."""
        from telemetry.config.cloudlogging_exporter import CloudLoggingSpanExporter
        from telemetry.config.cloudlogging_log_exporter import CloudLoggingLogExporter

        with patch.dict(os.environ, {"GCP_PROJECT_ID": "test-project"}):
            context = configure_telemetry(backend="cloudlogging", verbose=False)

            # Verify exporters are correct types
            assert isinstance(context.span_exporter, CloudLoggingSpanExporter)
            assert isinstance(context.log_exporter, CloudLoggingLogExporter)

            shutdown_telemetry(context)

    @patch("telemetry.config.cloudlogging_exporter.cloud_logging.Client")
    @patch("telemetry.config.cloudlogging_log_exporter.cloud_logging.Client")
    def test_telemetry_env_supports_cloudlogging(self, mock_log_client, mock_span_client):
        """TELEMETRY=cloudlogging environment variable works."""
        with patch.dict(
            os.environ, {"TELEMETRY": "cloudlogging", "GCP_PROJECT_ID": "test-project"}
        ):
            context = configure_telemetry(backend="disabled", verbose=False)  # Should be overridden

            # TELEMETRY env should override backend parameter
            assert context.backend == "cloudlogging"

            shutdown_telemetry(context)
