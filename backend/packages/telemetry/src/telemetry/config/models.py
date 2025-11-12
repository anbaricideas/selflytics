"""Pydantic models for OpenTelemetry data serialization to JSONL.

These models provide type-safe JSON encoding with support for datetime, bytes,
enums, and other non-JSON-serializable types that may appear in span/log data.
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_serializer


class SpanContext(BaseModel):
    """OpenTelemetry span context with trace and span IDs."""

    trace_id: str
    span_id: str
    trace_flags: int

    model_config = ConfigDict(frozen=True)


class SpanStatus(BaseModel):
    """OpenTelemetry span status information."""

    status_code: int | None = None
    description: str | None = None

    model_config = ConfigDict(frozen=True)


class SpanEvent(BaseModel):
    """OpenTelemetry span event with timestamp and attributes."""

    name: str
    timestamp: int  # nanoseconds since epoch
    attributes: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(frozen=True)

    @field_serializer("attributes")
    def serialize_attributes(self, value: dict[str, Any]) -> dict[str, Any]:
        """Serialize attribute values, handling datetime, bytes, and enums."""
        return {k: self._serialize_value(v) for k, v in value.items()}

    @staticmethod
    def _serialize_value(value: Any) -> Any:
        """Serialize a single value to JSON-compatible type."""
        if isinstance(value, datetime):
            return value.isoformat()
        if isinstance(value, bytes):
            return value.hex()
        if isinstance(value, Enum):
            return value.value
        return value


class SpanLink(BaseModel):
    """OpenTelemetry span link to another span."""

    context: SpanContext
    attributes: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(frozen=True)

    @field_serializer("attributes")
    def serialize_attributes(self, value: dict[str, Any]) -> dict[str, Any]:
        """Serialize attribute values, handling datetime, bytes, and enums."""
        return {k: SpanEvent._serialize_value(v) for k, v in value.items()}


class InstrumentationScope(BaseModel):
    """OpenTelemetry instrumentation scope information."""

    name: str | None = None
    version: str | None = None

    model_config = ConfigDict(frozen=True)


class SpanData(BaseModel):
    """Complete OpenTelemetry span data for JSONL serialization."""

    name: str
    context: SpanContext
    parent_span_id: str | None = None
    start_time: int  # nanoseconds since epoch
    end_time: int | None = None  # nanoseconds since epoch
    kind: int | None = None
    status: SpanStatus
    attributes: dict[str, Any] = Field(default_factory=dict)
    events: list[SpanEvent] = Field(default_factory=list)
    links: list[SpanLink] = Field(default_factory=list)
    resource: dict[str, Any] = Field(default_factory=dict)
    instrumentation_scope: InstrumentationScope

    model_config = ConfigDict(frozen=True)

    @field_serializer("attributes", "resource")
    def serialize_attributes(self, value: dict[str, Any]) -> dict[str, Any]:
        """Serialize attribute values, handling datetime, bytes, and enums."""
        return {k: SpanEvent._serialize_value(v) for k, v in value.items()}


class LogData(BaseModel):
    """Complete OpenTelemetry log record data for JSONL serialization."""

    timestamp: int  # nanoseconds since epoch
    observed_timestamp: int  # nanoseconds since epoch
    trace_id: str | None = None
    span_id: str | None = None
    trace_flags: int | None = None
    severity_text: str | None = None
    severity_number: int | None = None
    body: Any = None
    attributes: dict[str, Any] = Field(default_factory=dict)
    resource: dict[str, Any] = Field(default_factory=dict)
    scope: InstrumentationScope = Field(default_factory=InstrumentationScope)

    model_config = ConfigDict(frozen=True)

    @field_serializer("attributes", "resource")
    def serialize_attributes(self, value: dict[str, Any]) -> dict[str, Any]:
        """Serialize attribute values, handling datetime, bytes, and enums."""
        return {k: SpanEvent._serialize_value(v) for k, v in value.items()}

    @field_serializer("body")
    def serialize_body(self, value: Any) -> Any:
        """Serialize log body, handling datetime, bytes, and enums."""
        return SpanEvent._serialize_value(value)
