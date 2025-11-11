"""Application-level telemetry configuration for Selflytics."""

import logging
import os

from telemetry import TelemetryContext, configure_telemetry, shutdown_telemetry

from app.config import get_settings


logger = logging.getLogger(__name__)


def setup_telemetry() -> TelemetryContext:
    """Initialize telemetry based on application settings.

    Reads settings from app.config and environment variables,
    then configures the appropriate telemetry backend.

    Returns:
        TelemetryContext with session and exporter information
    """
    settings = get_settings()

    # Override backend from environment if set (already handled by Pydantic alias)
    backend = settings.telemetry_backend

    # NOTE: The telemetry package reads LOG_PATH and LOG_LEVEL from environment
    # variables rather than accepting them as parameters. This design decision
    # allows the package to remain decoupled from application-specific settings.
    # We set these env vars here to bridge the gap between FastAPI settings and
    # the telemetry package's expected configuration interface.

    # Set LOG_PATH environment variable for JSONL backend
    if backend == "jsonl":
        os.environ["LOG_PATH"] = settings.telemetry_log_path

    # Set LOG_LEVEL environment variable
    os.environ["LOG_LEVEL"] = settings.telemetry_log_level

    # Configure telemetry
    context = configure_telemetry(
        backend=backend,
        verbose=settings.telemetry_verbose,
    )

    if backend != "disabled":
        logger.info(
            "Telemetry configured: backend=%s, session_id=%s",
            backend,
            context.session_id,
        )

    return context


def teardown_telemetry(context: TelemetryContext) -> None:
    """Shutdown telemetry and release resources.

    Args:
        context: TelemetryContext from setup_telemetry()
    """
    if context.backend != "disabled":
        logger.info("Shutting down telemetry: session_id=%s", context.session_id)

    shutdown_telemetry(context)
