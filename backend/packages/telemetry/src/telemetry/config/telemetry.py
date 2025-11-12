"""
OpenTelemetry configuration for observability and debugging of CliniCraft WebApp.

This module provides configuration for various OpenTelemetry backends suitable for
local development and production use. It supports multiple backends to provide
flexibility in how traces are collected and analyzed.

Architecture:

This module uses a singleton pattern for OpenTelemetry providers to enable
reliable test execution in both sequential and parallel modes:

- Providers (TracerProvider, LoggerProvider) are created once per process
- Processors and exporters are created fresh for each telemetry session
- Processors are dynamically attached/removed from singleton providers
- This avoids OpenTelemetry's `_SET_ONCE` constraints while maintaining isolation

Process lifecycle:
1. First configure_telemetry() call creates providers (one-time setup)
2. Subsequent calls reuse providers, create new exporters/processors
3. shutdown_telemetry() removes processors, keeps providers alive
4. Providers are garbage collected on process exit

This design aligns with OpenTelemetry's provider singleton philosophy while
supporting test isolation and reconfiguration.

Supported backends:
- Console: Print traces to console (useful for debugging)
- JSONL: Local session-scoped JSONL files for persistent logging
- Cloud Logging: Native GCP integration for cloud-native observability
- Disabled: No telemetry (default, zero overhead)

Future backends:
- OTLP: Send traces to any OpenTelemetry Protocol endpoint
- GCS: Google Cloud Storage for production
"""

import atexit
import contextlib
import logging
import os
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from opentelemetry import _logs as logs_api
from opentelemetry import trace as trace_api
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.sdk import trace as trace_sdk
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs._internal import LogRecordProcessor
from opentelemetry.sdk._logs.export import (
    BatchLogRecordProcessor,
    LogExporter,
    SimpleLogRecordProcessor,
)
from opentelemetry.sdk.trace import SpanProcessor
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter,
    SimpleSpanProcessor,
    SpanExporter,
)

from telemetry.config.cloudlogging_exporter import CloudLoggingSpanExporter
from telemetry.config.cloudlogging_log_exporter import CloudLoggingLogExporter
from telemetry.config.jsonl_exporter import JSONLSpanExporter
from telemetry.config.jsonl_log_exporter import JSONLLogExporter


TelemetryBackend = Literal["console", "jsonl", "cloudlogging", "disabled"]


@dataclass
class TelemetryContext:
    """
    Context information for configured telemetry.

    Provides access to exporters, session information, and processor references
    for the configured telemetry backend.

    Note: File handles are managed internally by exporters via atexit hooks,
    not exposed in this context.
    """

    session_id: str
    log_file_path: Path | None
    span_exporter: SpanExporter | None
    backend: TelemetryBackend
    log_exporter: LogExporter | None = None

    # Processor references for cleanup (singleton pattern support)
    span_processor: SpanProcessor | None = None
    log_processor: LogRecordProcessor | None = None


# Global reference to current telemetry context
_current_telemetry_context: TelemetryContext | None = None

# Global singleton state (per-process)
_global_tracer_provider: trace_sdk.TracerProvider | None = None
_global_logger_provider: LoggerProvider | None = None
_provider_process_id: int | None = None  # For fork detection
_instrumentation_initialized: bool = False


def configure_telemetry(
    backend: TelemetryBackend = "disabled", verbose: bool = False
) -> TelemetryContext:
    """
    Configure OpenTelemetry tracing for the CliniCraft WebApp.

    This function sets up instrumentation to capture detailed traces of
    application behavior, API requests, and business logic execution.

    Lifecycle:
        This function should typically be called once at application startup.
        Multiple calls are supported but will accumulate resources - use
        shutdown_telemetry() to clean up before reconfiguring.

    Cleanup:
        Call shutdown_telemetry() with the returned TelemetryContext when
        shutting down your application to properly release resources.

    Args:
        backend: Which telemetry backend to use:
            - "console": Print traces to console output
            - "jsonl": Write to session-scoped JSONL files (local development)
            - "cloudlogging": Export to Google Cloud Logging (production)
            - "disabled": No tracing (default)
        verbose: Whether to print setup messages (default: False for silent operation)

    Returns:
        TelemetryContext with session information and exporters

    Environment Variables:
        - TELEMETRY: Backend type (overrides backend parameter)
        - LOG_PATH: Directory for JSONL files (default: ./logs)
        - LOG_LEVEL: Python log level (default: INFO)
        - GCP_PROJECT_ID: Required for cloudlogging backend
        - ENVIRONMENT: Environment name for cloudlogging (dev/staging/prod, default: dev)

    Example:
        >>> from telemetry import configure_telemetry, shutdown_telemetry
        >>>
        >>> # Configure console telemetry
        >>> context = configure_telemetry(backend="console", verbose=True)
        >>>
        >>> # Your application code here
        >>>
        >>> # Shutdown when done
        >>> shutdown_telemetry(context)
    """
    global _current_telemetry_context  # noqa: PLW0603

    # Allow TELEMETRY environment variable to override backend parameter
    env_backend = os.getenv("TELEMETRY")
    if env_backend:
        if env_backend not in ("console", "jsonl", "cloudlogging", "disabled"):
            raise ValueError(
                f"Invalid TELEMETRY environment variable: {env_backend!r}. "
                f"Valid options: 'console', 'jsonl', 'cloudlogging', 'disabled'"
            )
        backend = env_backend  # type: ignore[assignment]

    # Warn if reconfiguring without shutdown (orphaned processors)
    if _current_telemetry_context is not None and _current_telemetry_context.backend != "disabled":
        logger = logging.getLogger(__name__)
        logger.debug(
            "Reconfiguring telemetry from %s to %s without shutdown. "
            "Previous processors will be orphaned (still attached to providers). "
            "Call shutdown_telemetry() before reconfiguring to avoid processor accumulation.",
            _current_telemetry_context.backend,  # Internal enum, not user input
            backend,  # Internal enum, not user input
        )

    if backend == "disabled":
        _current_telemetry_context = TelemetryContext(
            session_id="disabled",
            log_file_path=None,
            span_exporter=None,
            backend="disabled",
            log_exporter=None,
        )
        return _current_telemetry_context

    if backend == "console":
        context = _configure_console(verbose=verbose)
    elif backend == "jsonl":
        context = _configure_jsonl(verbose=verbose)
    elif backend == "cloudlogging":
        context = _configure_cloudlogging(verbose=verbose)
    else:
        raise ValueError(f"Unsupported telemetry backend: {backend}")

    # Store context globally
    _current_telemetry_context = context

    return context


def shutdown_telemetry(context: TelemetryContext) -> None:
    """
    Shutdown telemetry session and clean up processors.

    In the singleton pattern, this function cleans up session-scoped resources
    (processors, exporters, file handles) while preserving process-scoped providers
    for reuse in subsequent sessions.

    Properly shuts down:
    - SpanProcessor (flushes and stops processing)
    - LogRecordProcessor (flushes and stops processing)
    - LoggingHandler (removes from root logger)
    - File handles (closes JSONL files)

    Does NOT shut down:
    - TracerProvider (reused across sessions)
    - LoggerProvider (reused across sessions)

    Args:
        context: TelemetryContext returned from configure_telemetry()
    """
    global _current_telemetry_context  # noqa: PLW0603

    if context.backend == "disabled":
        _current_telemetry_context = None
        return

    # Force flush processors before shutdown
    if context.span_processor:
        with contextlib.suppress(Exception):
            context.span_processor.force_flush(timeout_millis=5000)

    if context.log_processor:
        with contextlib.suppress(Exception):
            context.log_processor.force_flush(timeout_millis=5000)

    # Shutdown processors (closes exporters, stops background threads)
    # Note: OpenTelemetry providers don't have remove_processor methods,
    # so we just shutdown the processors. Providers hold dead references
    # which is acceptable - processors won't process after shutdown.
    if context.span_processor:
        with contextlib.suppress(Exception):
            context.span_processor.shutdown()

    if context.log_processor:
        with contextlib.suppress(Exception):
            context.log_processor.shutdown()

    # Remove LoggingHandler from root logger
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        if isinstance(handler, LoggingHandler):
            root_logger.removeHandler(handler)

    # Uninstrument logging (allow re-instrumentation in next session)
    global _instrumentation_initialized  # noqa: PLW0603
    try:
        LoggingInstrumentor().uninstrument()
        _instrumentation_initialized = False  # Allow re-instrumentation
    except RuntimeError:
        pass  # Already uninstrumented

    # Clear global context
    _current_telemetry_context = None

    # IMPORTANT: Keep providers alive for next session
    # Do NOT reset _global_tracer_provider or _global_logger_provider
    # Do NOT call provider.shutdown()
    # Providers will be reused or garbage collected on process exit


def _get_or_create_providers() -> tuple[trace_sdk.TracerProvider, LoggerProvider]:
    """
    Get existing providers or create them (once per process).

    This function implements the singleton pattern for OpenTelemetry providers,
    creating them once per process and reusing them across multiple telemetry
    sessions. This avoids OpenTelemetry's `_SET_ONCE` constraints that prevent
    provider reconfiguration.

    Returns:
        Tuple of (TracerProvider, LoggerProvider) - either existing or newly created

    Thread Safety:
        This function is NOT thread-safe. Call from single thread during
        application initialization. Concurrent calls may create duplicate providers.

    Fork Detection:
        If process ID changes (fork), new providers are created for the child process.
        This ensures each process has its own provider instances.
    """
    global _global_tracer_provider, _global_logger_provider, _provider_process_id  # noqa: PLW0603

    current_pid = os.getpid()

    # Check if providers exist AND we're in the same process
    if (
        _global_tracer_provider is not None
        and _global_logger_provider is not None
        and _provider_process_id == current_pid
    ):
        # Reuse existing providers
        return _global_tracer_provider, _global_logger_provider

    # Create new providers (first time or after fork)
    _global_tracer_provider = trace_sdk.TracerProvider()
    _global_logger_provider = LoggerProvider()
    _provider_process_id = current_pid

    # Set global providers (only happens once per process)
    trace_api.set_tracer_provider(_global_tracer_provider)
    logs_api.set_logger_provider(_global_logger_provider)

    return _global_tracer_provider, _global_logger_provider


def _attach_processors(
    tracer_provider: trace_sdk.TracerProvider,
    logger_provider: LoggerProvider,
    span_exporter: SpanExporter,
    log_exporter: LogExporter | None,
    backend: TelemetryBackend,
) -> tuple[SpanProcessor, LogRecordProcessor | None]:
    """
    Create and attach processors to providers.

    Creates processor instances for the given exporters and attaches them
    to the singleton providers. Each telemetry session gets fresh processors
    while reusing the same providers.

    Args:
        tracer_provider: TracerProvider to attach span processor to
        logger_provider: LoggerProvider to attach log processor to
        span_exporter: SpanExporter for span data
        log_exporter: LogExporter for log data (optional)
        backend: Backend type (affects processor choice)

    Returns:
        Tuple of (SpanProcessor, LogRecordProcessor or None)

    Note:
        Console backend uses SimpleSpanProcessor for immediate output.
        JSONL backend uses BatchSpanProcessor for efficiency.
    """
    # NOTE: OpenTelemetry providers accumulate processors - they cannot be removed,
    # only shutdown. After multiple configure/shutdown cycles, providers will hold
    # multiple shutdown processors. This is a bounded memory leak (processor objects
    # only, not telemetry data).
    #
    # Investigation (2025-11-07): OpenTelemetry's TracerProvider/LoggerProvider use
    # SynchronousMultiSpanProcessor internally, which stores processors in a tuple.
    # A workaround exists (manipulating _active_span_processor._span_processors), but
    # it relies on private attributes and is fragile across OpenTelemetry versions.
    #
    # Impact: Affects only test suites with many configure/shutdown cycles. Each
    # processor is <1KB, so 100 cycles = ~100KB overhead. Production apps typically
    # configure once per process lifetime, so no leak occurs in practice.
    #
    # Decision: Accept bounded leak as documented tradeoff. OpenTelemetry's design
    # intentionally prevents processor removal to maintain provider singleton semantics.

    # Create span processor (immediate for console, batched for JSONL/cloudlogging)
    span_processor: SpanProcessor
    if backend == "console":
        span_processor = SimpleSpanProcessor(span_exporter)
    else:
        span_processor = BatchSpanProcessor(span_exporter)

    # Attach span processor to provider
    tracer_provider.add_span_processor(span_processor)

    # Create and attach log processor if log exporter provided
    log_processor: LogRecordProcessor | None = None
    if log_exporter is not None:
        # Use immediate processing for console, batched for JSONL/cloudlogging
        if backend == "console":
            log_processor = SimpleLogRecordProcessor(log_exporter)
        else:
            log_processor = BatchLogRecordProcessor(
                log_exporter,
                max_export_batch_size=100,
                schedule_delay_millis=5000,
            )
        logger_provider.add_log_record_processor(log_processor)

    return span_processor, log_processor


def _register_flush_handler(
    span_processor: SpanProcessor | None, log_processor: LogRecordProcessor | None
) -> None:
    """
    Register atexit handler to flush telemetry processors on shutdown.

    Ensures all buffered telemetry data is flushed before process exit.
    This is critical for batch processors that buffer data before export.

    Args:
        span_processor: Span processor to flush, or None
        log_processor: Log processor to flush, or None
    """

    def _flush_telemetry() -> None:
        """Flush pending telemetry data before process exit."""
        if span_processor:
            span_processor.force_flush(timeout_millis=1000)
        if log_processor:
            log_processor.force_flush(timeout_millis=1000)

    atexit.register(_flush_telemetry)


def _configure_console(verbose: bool = True) -> TelemetryContext:
    """
    Configure console output as the telemetry backend.

    Uses singleton providers with SimpleSpanProcessor for immediate console output.
    """
    # Get or create singleton providers
    tracer_provider, logger_provider = _get_or_create_providers()

    # Create console exporter
    console_exporter = ConsoleSpanExporter()

    # Create and attach processor (SimpleSpanProcessor for immediate output)
    span_processor, _log_processor = _attach_processors(
        tracer_provider,
        logger_provider,
        console_exporter,
        log_exporter=None,  # Console backend doesn't export logs
        backend="console",
    )

    # Generate unique session ID with timestamp
    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S_%f")[:21]  # Include microseconds
    session_id = f"console_{timestamp}"

    if verbose:
        print("📝 Console tracing enabled - traces will be printed to stdout")  # noqa: T201

    return TelemetryContext(
        session_id=session_id,
        log_file_path=None,
        span_exporter=console_exporter,
        backend="console",
        log_exporter=None,
        span_processor=span_processor,
        log_processor=None,  # Console doesn't use log processor
    )


def _configure_jsonl(
    verbose: bool = False,
    session_id: str | None = None,
    log_path: str | None = None,
) -> TelemetryContext:
    """
    Configure JSONL file export as the telemetry backend.

    Sets up unified telemetry capture for both spans and logs to the same
    JSONL file with matching session IDs. Uses singleton providers to enable
    reconfiguration within the same process.

    Args:
        verbose: Whether to print setup messages
        session_id: Optional existing session ID (for subprocess reuse)
        log_path: Optional log directory path (for subprocess reuse)

    Returns:
        TelemetryContext with exporters configured for unified JSONL capture
    """

    # STEP 1: Get or create singleton providers
    tracer_provider, logger_provider = _get_or_create_providers()

    # STEP 2: Initialize LoggingInstrumentor (trace context in logs)
    global _instrumentation_initialized  # noqa: PLW0603
    if not _instrumentation_initialized:
        instrumentor = LoggingInstrumentor()
        if instrumentor.is_instrumented_by_opentelemetry:
            instrumentor.uninstrument()
        instrumentor.instrument(set_logging_format=True)
        _instrumentation_initialized = True

    # STEP 3: Get configuration (use provided or environment)
    if log_path is None:
        log_path = os.getenv("LOG_PATH", "./logs")

    # STEP 4: Configure logging level
    log_level = os.getenv("LOG_LEVEL", "INFO")
    try:
        numeric_level = getattr(logging, log_level.upper())
        logging.root.setLevel(numeric_level)
    except (AttributeError, ValueError):
        # Invalid log level, use default
        logging.root.setLevel(logging.INFO)

    # STEP 5: Generate or use provided session ID
    if session_id is None:
        # Use microsecond precision to prevent ID collisions in rapid configure/shutdown cycles
        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S_%f")[:21]  # Include microseconds
        session_id = f"session_{timestamp}"

    # STEP 6: Calculate log file path (before creating exporters)
    log_file_path = Path(log_path).resolve() / f"{session_id}.jsonl"

    # STEP 7: Create span exporter with session ID
    span_exporter = JSONLSpanExporter(
        session_id=session_id,
        log_path=log_path,
    )

    # STEP 8: Create log exporter with matching session ID
    log_exporter = JSONLLogExporter(
        session_id=session_id,
        log_path=log_path,
    )

    # STEP 8: Create and attach processors to singleton providers
    span_processor, log_processor = _attach_processors(
        tracer_provider,
        logger_provider,
        span_exporter,
        log_exporter,
        backend="jsonl",
    )

    # STEP 9: Attach LoggingHandler to root logger
    # Remove any existing LoggingHandler instances to prevent duplicates
    root_logger = logging.getLogger()
    for existing_handler in root_logger.handlers[:]:
        if isinstance(existing_handler, LoggingHandler):
            root_logger.removeHandler(existing_handler)

    # This captures all Python logging calls and forwards to OpenTelemetry
    handler = LoggingHandler(level=logging.NOTSET, logger_provider=logger_provider)
    root_logger.addHandler(handler)

    # STEP 10: Register atexit handler to flush on subprocess exit
    _register_flush_handler(span_processor, log_processor)

    if verbose:
        print(f"📝 JSONL tracing enabled - session: {session_id}")  # noqa: T201
        print(f"📁 Log directory: {log_path}")  # noqa: T201
        print("✅ Capturing spans + logs to JSONL")  # noqa: T201

    # Return telemetry context with all components INCLUDING processors
    return TelemetryContext(
        session_id=session_id,
        log_file_path=log_file_path,
        span_exporter=span_exporter,
        backend="jsonl",
        log_exporter=log_exporter,
        span_processor=span_processor,
        log_processor=log_processor,
    )


def _configure_cloudlogging(verbose: bool = False) -> TelemetryContext:
    """
    Configure Google Cloud Logging as the telemetry backend.

    Sets up telemetry export to Cloud Logging for cloud-native observability.
    Uses singleton providers with batch processors for efficient cloud export.

    Args:
        verbose: Whether to print setup messages

    Returns:
        TelemetryContext with exporters configured for Cloud Logging

    Environment Variables:
        - GCP_PROJECT_ID: Required GCP project ID for Cloud Logging
        - ENVIRONMENT: Environment name (dev/staging/prod), default: dev

    Raises:
        ValueError: If GCP_PROJECT_ID environment variable is not set
    """
    # STEP 1: Get or create singleton providers
    tracer_provider, logger_provider = _get_or_create_providers()

    # STEP 2: Initialize LoggingInstrumentor (trace context in logs)
    global _instrumentation_initialized  # noqa: PLW0603
    if not _instrumentation_initialized:
        instrumentor = LoggingInstrumentor()
        if instrumentor.is_instrumented_by_opentelemetry:
            instrumentor.uninstrument()
        instrumentor.instrument(set_logging_format=True)
        _instrumentation_initialized = True

    # STEP 3: Get required configuration from environment
    project_id = os.getenv("GCP_PROJECT_ID")
    if not project_id:
        raise ValueError("GCP_PROJECT_ID environment variable is required for cloudlogging backend")

    environment = os.getenv("ENVIRONMENT", "dev")

    # STEP 4: Configure logging level
    log_level = os.getenv("LOG_LEVEL", "INFO")
    try:
        numeric_level = getattr(logging, log_level.upper())
        logging.root.setLevel(numeric_level)
    except (AttributeError, ValueError):
        # Invalid log level, use default
        logging.root.setLevel(logging.INFO)

    # STEP 5: Generate session ID
    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S_%f")[:21]
    session_id = f"cloudlogging_{timestamp}"

    # STEP 6: Create Cloud Logging exporters
    span_exporter = CloudLoggingSpanExporter(
        project_id=project_id,
        environment=environment,
    )
    log_exporter = CloudLoggingLogExporter(
        project_id=project_id,
        environment=environment,
    )

    # STEP 7: Create and attach processors to singleton providers
    span_processor, log_processor = _attach_processors(
        tracer_provider,
        logger_provider,
        span_exporter,
        log_exporter,
        backend="cloudlogging",
    )

    # STEP 8: Attach LoggingHandler to root logger
    # Remove any existing LoggingHandler instances to prevent duplicates
    root_logger = logging.getLogger()
    for existing_handler in root_logger.handlers[:]:
        if isinstance(existing_handler, LoggingHandler):
            root_logger.removeHandler(existing_handler)

    # This captures all Python logging calls and forwards to OpenTelemetry
    handler = LoggingHandler(level=logging.NOTSET, logger_provider=logger_provider)
    root_logger.addHandler(handler)

    # STEP 9: Register atexit handler to flush on process exit
    _register_flush_handler(span_processor, log_processor)

    if verbose:
        print(f"📝 Cloud Logging enabled - project: {project_id}, environment: {environment}")  # noqa: T201
        print("✅ Capturing spans + logs to Cloud Logging")  # noqa: T201

    # Return telemetry context
    return TelemetryContext(
        session_id=session_id,
        log_file_path=None,  # No local file for Cloud Logging
        span_exporter=span_exporter,
        backend="cloudlogging",
        log_exporter=log_exporter,
        span_processor=span_processor,
        log_processor=log_processor,
    )
