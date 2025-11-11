"""
Unit tests for telemetry package public API.

Tests verify that all public functions and classes are properly exported
from the top-level telemetry package and can be imported directly.
"""


class TestPublicAPIExports:
    """Tests for public API exports from telemetry package."""

    def test_configure_telemetry_is_exported(self) -> None:
        """configure_telemetry function is accessible from top-level import."""
        from telemetry import configure_telemetry

        assert callable(configure_telemetry)
        assert configure_telemetry.__name__ == "configure_telemetry"

    def test_shutdown_telemetry_is_exported(self) -> None:
        """shutdown_telemetry function is accessible from top-level import."""
        from telemetry import shutdown_telemetry

        assert callable(shutdown_telemetry)
        assert shutdown_telemetry.__name__ == "shutdown_telemetry"

    def test_telemetry_context_is_exported(self) -> None:
        """TelemetryContext class is accessible from top-level import."""
        from telemetry import TelemetryContext

        assert TelemetryContext.__name__ == "TelemetryContext"
        # Verify it's a dataclass
        assert hasattr(TelemetryContext, "__dataclass_fields__")

    def test_telemetry_backend_is_exported(self) -> None:
        """TelemetryBackend type alias is accessible from top-level import."""
        from telemetry import TelemetryBackend

        # TelemetryBackend is a Literal type alias
        assert TelemetryBackend is not None

    def test_redact_string_is_exported(self) -> None:
        """redact_string function is accessible from top-level import."""
        from telemetry import redact_string

        assert callable(redact_string)
        assert redact_string.__name__ == "redact_string"

    def test_redact_for_logging_is_exported(self) -> None:
        """redact_for_logging function is accessible from top-level import."""
        from telemetry import redact_for_logging

        assert callable(redact_for_logging)
        assert redact_for_logging.__name__ == "redact_for_logging"

    def test_all_exports_listed_in_dunder_all(self) -> None:
        """All public exports are listed in __all__."""
        import telemetry

        assert hasattr(telemetry, "__all__")
        expected_exports = {
            "TelemetryBackend",
            "TelemetryContext",
            "configure_telemetry",
            "shutdown_telemetry",
            "redact_string",
            "redact_for_logging",
        }
        assert set(telemetry.__all__) == expected_exports

    def test_version_is_defined(self) -> None:
        """Package version is defined in __version__."""
        import telemetry

        assert hasattr(telemetry, "__version__")
        assert isinstance(telemetry.__version__, str)
        assert len(telemetry.__version__) > 0

    def test_star_import_only_exports_public_api(self) -> None:
        """Star import (from telemetry import *) only imports __all__ items."""
        import telemetry

        # Simulate star import by checking __all__
        star_imports = set(telemetry.__all__)
        expected = {
            "TelemetryBackend",
            "TelemetryContext",
            "configure_telemetry",
            "shutdown_telemetry",
            "redact_string",
            "redact_for_logging",
        }
        assert star_imports == expected


class TestPublicAPIFunctionality:
    """Tests that verify exported functions actually work."""

    def test_configure_telemetry_works_from_toplevel_import(self) -> None:
        """configure_telemetry works when imported from top level."""
        from telemetry import configure_telemetry, shutdown_telemetry

        context = configure_telemetry(backend="disabled")
        assert context.backend == "disabled"
        shutdown_telemetry(context)

    def test_redact_string_works_from_toplevel_import(self) -> None:
        """redact_string works when imported from top level."""
        from telemetry import redact_string

        result = redact_string("secret123")
        assert result == "s*******3"

    def test_redact_for_logging_works_from_toplevel_import(self) -> None:
        """redact_for_logging works when imported from top level."""
        from telemetry import redact_for_logging

        result = redact_for_logging("api_key_12345")
        assert result == "a***********5"

    def test_telemetry_context_can_be_instantiated(self) -> None:
        """TelemetryContext can be created from top-level import."""
        from telemetry import TelemetryContext

        context = TelemetryContext(
            session_id="test",
            log_file_path=None,
            span_exporter=None,
            backend="disabled",
        )
        assert context.session_id == "test"
        assert context.backend == "disabled"


class TestPublicAPIDocumentation:
    """Tests that verify public API has proper documentation."""

    def test_package_has_docstring(self) -> None:
        """Telemetry package has a module-level docstring."""
        import telemetry

        assert telemetry.__doc__ is not None
        assert len(telemetry.__doc__) > 0

    def test_configure_telemetry_has_docstring(self) -> None:
        """configure_telemetry function has documentation."""
        from telemetry import configure_telemetry

        assert configure_telemetry.__doc__ is not None
        assert "Configure OpenTelemetry" in configure_telemetry.__doc__

    def test_shutdown_telemetry_has_docstring(self) -> None:
        """shutdown_telemetry function has documentation."""
        from telemetry import shutdown_telemetry

        assert shutdown_telemetry.__doc__ is not None
        assert "Shutdown telemetry" in shutdown_telemetry.__doc__

    def test_redact_string_has_docstring(self) -> None:
        """redact_string function has documentation."""
        from telemetry import redact_string

        assert redact_string.__doc__ is not None
        assert "redact" in redact_string.__doc__.lower()

    def test_redact_for_logging_has_docstring(self) -> None:
        """redact_for_logging function has documentation."""
        from telemetry import redact_for_logging

        assert redact_for_logging.__doc__ is not None
        assert "redact" in redact_for_logging.__doc__.lower()
