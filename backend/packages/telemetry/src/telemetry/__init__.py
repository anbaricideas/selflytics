"""Production-grade telemetry for CliniCraft WebApp.

This package provides OpenTelemetry-based telemetry with multiple backends
for local development and production use. It includes structured logging,
automatic trace correlation, and security utilities for PII redaction.

Features:
- Multiple backends: Console (stdout), JSONL (local files), Cloud Logging (GCP), Disabled (no-op)
- Automatic trace_id/span_id injection for request correlation
- Thread-safe span and log exporters
- Environment variable configuration
- PII redaction utilities for secure logging
- Zero overhead when disabled

Quick Start:
    >>> from telemetry import configure_telemetry, shutdown_telemetry
    >>>
    >>> # Configure console telemetry for development
    >>> context = configure_telemetry(backend="console", verbose=True)
    >>>
    >>> # Your application code here
    >>>
    >>> # Cleanup when done
    >>> shutdown_telemetry(context)

Environment Variables:
    TELEMETRY: Backend type (console|jsonl|cloudlogging|disabled) - overrides backend parameter
    LOG_PATH: Directory for JSONL files (default: ./logs)
    LOG_LEVEL: Python log level (default: INFO)
    GCP_PROJECT_ID: Required for cloudlogging backend
    ENVIRONMENT: Environment name for cloudlogging (dev/staging/prod, default: dev)

See Also:
    configure_telemetry: Main configuration function
    shutdown_telemetry: Cleanup and resource release
    TelemetryContext: Configuration context dataclass
    redact_string: Redact sensitive strings for logging
    redact_for_logging: Redact any value for safe logging
"""

from telemetry.config.telemetry import (
    TelemetryBackend,
    TelemetryContext,
    configure_telemetry,
    shutdown_telemetry,
)
from telemetry.logging_utils import redact_for_logging, redact_string


__all__ = [
    "TelemetryBackend",
    "TelemetryContext",
    "configure_telemetry",
    "redact_for_logging",
    "redact_string",
    "shutdown_telemetry",
]

__version__ = "0.1.0"
