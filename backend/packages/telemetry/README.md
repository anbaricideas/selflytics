# CliniCraft Telemetry Package

Production-grade telemetry for CliniCraft WebApp, providing structured logging, OpenTelemetry-based trace correlation, and multiple backend support for local development and production environments.

## Features

- **Multiple Backends**: Console (stdout), JSONL (local files), Cloud Logging (GCP), Disabled (no-op)
- **Trace Correlation**: Automatic trace_id/span_id injection for request correlation
- **Cloud Native**: First-class Google Cloud Logging integration for production environments
- **Security First**: PII redaction utilities for safe logging
- **Production Ready**: Based on proven Garmin Agents implementation (1,000+ lines of production code)
- **Zero Overhead**: Disabled backend has no performance impact
- **Thread-Safe**: All exporters use locks for concurrent write safety
- **Test Coverage**: 80%+ coverage with comprehensive behavioral tests

## Installation

This package is part of the CliniCraft monorepo. It's automatically available when working within the backend environment:

```bash
# From project root
cd backend
uv sync --all-extras
```

## Quick Start

### Console Backend (Development)

Print traces to stdout for immediate debugging:

```python
from telemetry import configure_telemetry, shutdown_telemetry

# Configure console telemetry
context = configure_telemetry(backend="console", verbose=True)

# Your application code here
# All spans will be printed to stdout

# Shutdown when done
shutdown_telemetry(context)
```

### JSONL Backend (Local Persistence)

Write traces to local JSONL files for analysis:

```python
import os
from telemetry import configure_telemetry, shutdown_telemetry

# Configure JSONL telemetry
os.environ["LOG_PATH"] = "./logs"
context = configure_telemetry(backend="jsonl", verbose=True)

# Your application code here
# Logs written to ./logs/{session_id}.jsonl

# Shutdown when done
shutdown_telemetry(context)
```

### Cloud Logging Backend (Production)

For deployed environments (Cloud Run, GKE, Compute Engine), use the Cloud Logging backend to send telemetry data directly to Google Cloud Logging:

```python
import os
from telemetry import configure_telemetry, shutdown_telemetry

# Configure Cloud Logging telemetry
os.environ["GCP_PROJECT_ID"] = "your-project-id"
os.environ["ENVIRONMENT"] = "dev"  # or staging, prod
context = configure_telemetry(backend="cloudlogging", verbose=True)

# Your application code here
# Logs and spans written to Cloud Logging: projects/PROJECT_ID/logs/clinicraft-{environment}

# Shutdown when done
shutdown_telemetry(context)
```

**Environment Variables:**
- `GCP_PROJECT_ID` (required): GCP project ID
- `ENVIRONMENT` (optional): Environment name (default: "dev")
- `LOG_LEVEL` (optional): Log level (default: DEBUG for dev, INFO for staging/prod)

**Log Structure:**

Logs are written to Cloud Logging with full trace correlation:
- **Log name**: `projects/PROJECT_ID/logs/clinicraft-{environment}`
- **Trace**: `projects/PROJECT_ID/traces/{trace_id}`
- **Span ID**: Included for correlation
- **Payload**: Structured JSON with all event data

**Querying Logs:**

```bash
# List recent logs
gcloud logging read "logName=projects/PROJECT_ID/logs/clinicraft-dev" --limit=10

# Query by trace ID
gcloud logging read "logName=projects/PROJECT_ID/logs/clinicraft-dev AND jsonPayload.trace_id=\"abc123\"" --format=json

# Filter by severity
gcloud logging read "logName=projects/PROJECT_ID/logs/clinicraft-dev AND severity>=ERROR" --limit=20
```

**Retention:**
- Dev: 7 days (configurable)
- Staging: 7 days (configurable)
- Prod: 30 days (configurable up to 365 days for compliance)

See [Cloud Logging Deployment Guide](../../../docs/development/telemetry-cloud-logging/DEPLOYMENT.md) for setup instructions.

### Disabled Backend (Minimal Overhead)

Zero-overhead no-op for environments where telemetry is not needed:

```python
from telemetry import configure_telemetry

# No-op configuration (zero overhead)
context = configure_telemetry(backend="disabled")
```

## Environment Variables

Control telemetry behavior via environment variables:

| Variable | Values | Default | Description |
|----------|--------|---------|-------------|
| `TELEMETRY` | `console`, `jsonl`, `cloudlogging`, `disabled` | `disabled` | Backend type (overrides parameter) |
| `LOG_PATH` | Directory path | `./logs` | Directory for JSONL files |
| `GCP_PROJECT_ID` | GCP project ID | (none) | Required for Cloud Logging backend |
| `ENVIRONMENT` | `dev`, `staging`, `prod` | `dev` | Environment name (affects log name and retention) |
| `LOG_LEVEL` | `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` | `INFO` | Python logging level |

> **Note on GCP Environment Variables:** The telemetry package uses `GCP_PROJECT_ID`
> (not `GOOGLE_CLOUD_PROJECT` from app config) to maintain separation between
> application-level GCP integrations and telemetry-specific configuration. This allows
> the telemetry system to be independently configured without affecting application behavior.

### Example

```bash
# Enable JSONL telemetry with debug logging
export TELEMETRY=jsonl
export LOG_PATH=./telemetry_logs
export LOG_LEVEL=DEBUG

# Run your application
uv run --directory backend uvicorn app.main:app
```

## API Reference

### configure_telemetry

Configure OpenTelemetry tracing for the application.

```python
def configure_telemetry(
    backend: TelemetryBackend = "disabled",
    verbose: bool = False
) -> TelemetryContext
```

**Parameters:**
- `backend`: Which telemetry backend to use (`console`, `jsonl`, `cloudlogging`, or `disabled`)
- `verbose`: Whether to print setup messages (default: False)

**Returns:**
- `TelemetryContext` with session information and exporters

**Environment Variables:**
- `TELEMETRY`: Overrides backend parameter
- `LOG_PATH`: Directory for JSONL files (default: ./logs)
- `LOG_LEVEL`: Python log level (default: INFO)

### shutdown_telemetry

Shutdown telemetry session and clean up resources.

```python
def shutdown_telemetry(context: TelemetryContext) -> None
```

**Parameters:**
- `context`: TelemetryContext returned from `configure_telemetry()`

**Notes:**
- Flushes all pending telemetry data
- Closes file handles (JSONL backend)
- Removes processors from providers
- Keeps providers alive for potential reuse

### TelemetryContext

Dataclass containing telemetry configuration information.

```python
@dataclass
class TelemetryContext:
    session_id: str                          # Unique session identifier
    log_file_path: Path | None               # Path to JSONL file (if applicable)
    span_exporter: SpanExporter | None       # OpenTelemetry span exporter
    backend: TelemetryBackend                # Backend type
    log_exporter: LogExporter | None         # OpenTelemetry log exporter
    span_processor: SpanProcessor | None     # Span processor instance
    log_processor: LogRecordProcessor | None # Log processor instance
```

### redact_string

Redact a string for safe logging, showing only first and last characters.

```python
def redact_string(value: str | None, min_visible_chars: int = 1) -> str
```

**Examples:**
```python
from telemetry import redact_string

redact_string("secret123")        # "s*******3"
redact_string("api_key_12345")    # "a***********5"
redact_string("xy")               # "x*y"
redact_string("a")                # "*"
redact_string(None)               # "<None>"
redact_string("")                 # "<empty>"
```

### redact_for_logging

Redact any value for safe logging (strings, numbers, None).

```python
def redact_for_logging(value: str | int | float | None) -> str
```

**Examples:**
```python
from telemetry import redact_for_logging

redact_for_logging("password123")  # "p*********3"
redact_for_logging(12345)          # "1***5"
redact_for_logging(3.14159)        # "3*****9"
redact_for_logging(None)           # "<None>"
```

## Backend Comparison

| Feature | Console | JSONL | Cloud Logging | Disabled |
|---------|---------|-------|---------------|----------|
| **Output** | stdout | Local files | Google Cloud Logging | None |
| **Persistence** | No | Yes | Yes (7-365 days) | No |
| **Performance** | Medium | Medium | Medium | Zero overhead |
| **Use Case** | Development debugging | Local analysis | Production monitoring | Minimal overhead environments |
| **Storage** | N/A | ~1-10 MB/session | Managed by GCP | N/A |
| **Thread-Safe** | Yes | Yes | Yes | Yes |
| **Querying** | N/A | jq/grep | Cloud Console + gcloud CLI | N/A |
| **Cost** | Free | Disk space | GCP pricing (first 50 GB/month free) | Free |

## Security Considerations

### PII Redaction

Always use redaction utilities when logging sensitive data:

```python
from telemetry import redact_string, redact_for_logging

# Redact API keys, passwords, tokens
api_key = os.getenv("API_KEY")
logger.info(f"Using API key: {redact_string(api_key)}")

# Redact user IDs, emails, phone numbers
user_id = request.headers.get("X-User-ID")
logger.info(f"Request from user: {redact_for_logging(user_id)}")
```

### Pre-commit Enforcement

The project includes pre-commit hooks that enforce security best practices:

- **Bandit**: Scans for security issues
- **Ruff**: Checks for hardcoded secrets
- **Custom validators**: Block common PII patterns

### File Permissions

JSONL telemetry files may contain sensitive application data. Ensure appropriate file permissions in production:

**Unix/Linux:**
```bash
# Restrict log directory to application user only
chmod 700 /path/to/logs
chmod 600 /path/to/logs/*.jsonl
```

**Docker/Cloud Run:**
```dockerfile
# Set restrictive permissions in Dockerfile
RUN mkdir -p /app/logs && chmod 700 /app/logs
USER nonroot  # Run as non-root user
```

**Best Practices:**
- Log files should be readable only by the application user
- Log directory should not be world-readable
- Consider encrypting logs at rest for highly sensitive data
- Rotate and purge old logs regularly

## Development

### Running Tests

```bash
# Run all telemetry package tests
uv run pytest backend/packages/telemetry/tests -v

# Run with coverage
uv run pytest backend/packages/telemetry/tests --cov=telemetry --cov-report=term-missing

# Run specific test file
uv run pytest backend/packages/telemetry/tests/unit/test_telemetry_config.py -v
```

### Type Checking

```bash
# Type check the telemetry package
uv run mypy backend/packages/telemetry/src --strict
```

### Linting and Formatting

```bash
# Check code quality
uv run ruff check backend/packages/telemetry/

# Auto-fix issues
uv run ruff check backend/packages/telemetry/ --fix

# Format code
uv run ruff format backend/packages/telemetry/
```

### Pre-commit Hooks

```bash
# Run all pre-commit hooks manually
uv run pre-commit run --all-files

# Run on telemetry files only
uv run pre-commit run --files backend/packages/telemetry/**/*
```

## Architecture

### Singleton Provider Pattern

The package uses a singleton pattern for OpenTelemetry providers to enable test isolation and reconfiguration:

- **Providers** (TracerProvider, LoggerProvider) are created once per process
- **Processors** and **Exporters** are created fresh for each telemetry session
- Processors are dynamically attached/removed from singleton providers
- This avoids OpenTelemetry's `_SET_ONCE` constraints

### Lifecycle

1. First `configure_telemetry()` call creates providers (one-time setup)
2. Subsequent calls reuse providers, create new exporters/processors
3. `shutdown_telemetry()` removes processors, keeps providers alive
4. Providers are garbage collected on process exit

### Thread Safety

All exporters use `threading.Lock` for concurrent write safety:

- **JSONL Exporters**: Lock protects file write operations
- **Processors**: Use OpenTelemetry's built-in thread safety
- **Provider Attachment**: Not thread-safe, call from single thread during initialization

## Troubleshooting

### JSONL Files Not Created

**Problem**: No files appear in `LOG_PATH` directory

**Solution**:
1. Check `LOG_PATH` environment variable is set correctly
2. Verify directory has write permissions
3. Ensure `configure_telemetry(backend="jsonl")` was called
4. Call `shutdown_telemetry()` or `context.span_processor.force_flush()` to flush buffers

### Spans Not Appearing in Console

**Problem**: Console backend configured but no output visible

**Solution**:
1. Verify `backend="console"` was used (not `"disabled"`)
2. Check that spans are actually being created (use `tracer.start_as_current_span()`)
3. Console output may be buffered - call `force_flush()` to see immediate output
4. SimpleSpanProcessor exports synchronously when span ends

### Invalid LOG_LEVEL

**Problem**: Invalid `LOG_LEVEL` environment variable

**Solution**:
- Use valid Python logging levels: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`
- Invalid values fall back to `INFO` (no error raised)

### Memory Growth from Multiple Sessions

**Problem**: Memory grows after many `configure_telemetry()` / `shutdown_telemetry()` cycles

**Explanation**:
- OpenTelemetry providers accumulate shutdown processors (bounded memory leak)
- This is by design - providers cannot remove processors, only shutdown them
- For long-running processes, minimize reconfiguration cycles

**Solution**:
- Configure telemetry once at application startup
- Reuse the same context for the lifetime of the process
- Only shutdown on application teardown

## Examples

### FastAPI Integration

Configure telemetry at application startup and add request tracing middleware:

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.middleware.telemetry import TelemetryMiddleware
from telemetry import configure_telemetry, shutdown_telemetry

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: configure telemetry
    context = configure_telemetry(backend="jsonl", verbose=True)
    app.state.telemetry_context = context
    yield
    # Shutdown: cleanup telemetry
    shutdown_telemetry(context)

app = FastAPI(lifespan=lifespan)

# Add telemetry middleware for request tracing
app.add_middleware(
    TelemetryMiddleware,
    skip_paths={"/health"},  # Optional: skip health checks
)
```

### Request Tracing Middleware

The `TelemetryMiddleware` automatically captures telemetry for all HTTP requests:

**Features:**
- Logs request method, path, and timestamp
- Captures response status code
- Measures request duration in milliseconds
- Extracts OpenTelemetry trace_id and span_id for correlation
- Handles exceptions with full trace context
- Optional path filtering to reduce noise (e.g., health checks)

**Log Fields:**
- `method`: HTTP method (GET, POST, etc.)
- `path`: Request path
- `status_code`: Response status code
- `duration_ms`: Request processing time in milliseconds
- `trace_id`: OpenTelemetry trace ID for correlation
- `span_id`: OpenTelemetry span ID for correlation
- `error`: Error message (for exceptions)

**Example Log Output (JSONL):**
```json
{
  "timestamp": "2025-11-07T12:34:56.789Z",
  "severity_text": "INFO",
  "body": "Request completed",
  "attributes": {
    "method": "GET",
    "path": "/api/content",
    "status_code": 200,
    "duration_ms": 12.34,
    "trace_id": "5ce0e9a56015fec5adb25b99f6fa6a59",
    "span_id": "000067fd90b8f0"
  }
}
```

**Trace Correlation:**

All logs for a single request share the same `trace_id`, allowing you to:
- Track a request through the entire system
- Correlate logs from different components
- Debug complex request flows
- Filter logs by trace_id to see complete request lifecycle

**Example:**
```bash
# View all logs for a specific trace
cat logs/session_*.jsonl | jq 'select(.attributes.trace_id == "5ce0e9a56015fec5adb25b99f6fa6a59")'
```

**Exception Tracing:**

When exceptions occur, the middleware logs them with full trace context:

```json
{
  "timestamp": "2025-11-07T12:34:56.789Z",
  "severity_text": "ERROR",
  "body": "Request failed",
  "attributes": {
    "method": "POST",
    "path": "/api/generate",
    "duration_ms": 5.67,
    "trace_id": "abc123...",
    "span_id": "def456...",
    "error": "ValueError: Invalid input parameters"
  },
  "exc_info": "..."
}
```

**Performance Impact:**

The `TelemetryMiddleware` adds minimal overhead to request processing:

- **Latency**: ~0.1-0.5ms per request (primarily logging I/O)
- **Skip paths**: Near-zero overhead (<0.01ms) for filtered paths like `/health`
- **Memory**: Negligible (trace context extraction is lightweight)
- **Async-safe**: All operations are async-compatible

**Performance tips:**
- Use skip_paths to filter high-frequency monitoring endpoints
- JSONL backend writes are buffered (flush on shutdown)
- Console backend is synchronous but fast (stdout writes are buffered by OS)
- For high-traffic applications (>1000 req/s), consider async log handlers

**Benchmark (FastAPI TestClient, 1000 requests)**:
- Without middleware: ~50ms total
- With middleware (console): ~55ms total (+10% overhead)
- With middleware (disabled): ~50ms total (<1% overhead)
- With middleware (JSONL): ~60ms total (+20% overhead, includes file I/O)

### Frontend Telemetry Integration

The telemetry system includes a FastAPI endpoint for capturing frontend events with automatic trace correlation. This allows client-side telemetry to be logged through the same backend as server-side telemetry.

**Endpoint**: `POST /api/telemetry/log`

**Request Schema**:
```json
{
  "event_type": "user_action",           // Required: Event type (e.g., user_action, error, performance)
  "trace_id": "optional-trace-id",       // Optional: Trace ID for correlation (auto-generated if missing)
  "data": {                               // Required: Event-specific payload (any JSON object)
    "action": "click",
    "button": "submit",
    "page": "/dashboard"
  },
  "timestamp": "2025-11-08T12:34:56.789Z" // Optional: ISO 8601 timestamp (server-generated if missing)
}
```

**Response Schema**:
```json
{
  "trace_id": "abc123def456...",          // 32-char hex trace ID for client-side correlation
  "status": "logged"                       // Status of log operation
}
```

**Trace Correlation**:

Frontend events are automatically correlated with backend events:
1. If `trace_id` is provided in the request, it's used for correlation
2. If `X-Cloud-Trace-Context` header is present, trace is extracted
3. If neither is provided, a new trace_id is generated
4. The trace_id is returned in the response for client-side storage

**Usage Example (JavaScript)**:

```javascript
// Send frontend telemetry event
async function logTelemetryEvent(eventType, data) {
  const response = await fetch('/api/telemetry/log', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      event_type: eventType,
      data: data
    })
  });

  const result = await response.json();
  // Store trace_id for session correlation
  sessionStorage.setItem('trace_id', result.trace_id);
  return result;
}

// Example: Log user action
await logTelemetryEvent('user_action', {
  action: 'generate_content',
  content_type: 'blog_post',
  duration_ms: 1234
});

// Example: Log performance metric
await logTelemetryEvent('performance', {
  metric: 'page_load_time',
  value: 2.5,
  page: window.location.pathname
});

// Example: Log error with trace correlation
const traceId = sessionStorage.getItem('trace_id');
await fetch('/api/telemetry/log', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    event_type: 'error',
    trace_id: traceId,  // Correlate with previous events
    data: {
      message: error.message,
      stack: error.stack,
      page: window.location.pathname
    }
  })
});
```

**Backend Logging**:

All frontend events are logged through the configured telemetry backend (JSONL for local dev, Cloud Logging for deployed environments) with the following structure:

```json
{
  "timestamp": "2025-11-08T12:34:56.789Z",
  "severity_text": "INFO",
  "body": "Frontend telemetry event",
  "attributes": {
    "event_type": "user_action",
    "trace_id": "abc123def456...",
    "source": "frontend",
    "action": "generate_content",
    "content_type": "blog_post",
    "duration_ms": 1234
  }
}
```

**Querying Frontend Events**:

In Cloud Logging:
```bash
# Query all frontend events
gcloud logging read "logName=projects/PROJECT_ID/logs/clinicraft-dev AND jsonPayload.source=\"frontend\"" --limit=20

# Query by trace ID (correlate frontend and backend events)
gcloud logging read "logName=projects/PROJECT_ID/logs/clinicraft-dev AND jsonPayload.trace_id=\"abc123def456...\"" --format=json

# Query by event type
gcloud logging read "logName=projects/PROJECT_ID/logs/clinicraft-dev AND jsonPayload.source=\"frontend\" AND jsonPayload.event_type=\"error\"" --limit=10
```

In local JSONL files:
```bash
# Find all frontend events
cat logs/*.jsonl | jq 'select(.attributes.source == "frontend")'

# Find events by trace ID
cat logs/*.jsonl | jq 'select(.attributes.trace_id == "abc123def456...")'
```

**Security Considerations**:

- The endpoint validates all inputs using Pydantic schemas
- Trace IDs are validated (32-char lowercase hex)
- Invalid trace IDs are regenerated (not rejected)
- No PII should be sent from the frontend
- Rate limiting should be implemented for production use

### Session Export and Debugging

For Cloud Logging backend, use session export utilities to retrieve and analyze telemetry data locally. These scripts are essential for debugging production issues and analyzing user sessions.

**Quick Start**:

```bash
# List recent sessions from last 24 hours
./scripts/list-sessions.sh dev 24

# Export a specific session for analysis
TRACE_ID=$(./scripts/list-sessions.sh dev 24 | head -n 1)
./scripts/export-session.sh "$TRACE_ID" dev

# Analyze exported session with jq
cat session_exports/session_${TRACE_ID}.json | jq '.[] | {
  timestamp,
  message: .jsonPayload.message,
  severity
}'
```

**Available Scripts**:

1. **`list-sessions.sh`** - List trace IDs from Cloud Logging
   ```bash
   # Usage: ./scripts/list-sessions.sh [environment] [hours_ago]

   # List sessions from dev (default 24 hours)
   ./scripts/list-sessions.sh dev

   # List sessions from staging, last 12 hours
   ./scripts/list-sessions.sh staging 12
   ```

2. **`export-session.sh`** - Export session logs to JSON file
   ```bash
   # Usage: ./scripts/export-session.sh <trace_id> [environment] [output_dir]

   # Export to default directory (./session_exports)
   ./scripts/export-session.sh <trace_id> dev

   # Export to custom directory
   ./scripts/export-session.sh <trace_id> dev /tmp/debug
   ```

**Common Analysis Tasks**:

```bash
# Find all errors in a session
cat session_exports/session_${TRACE_ID}.json | jq '.[] | select(.severity == "ERROR")'

# Extract performance metrics
cat session_exports/session_${TRACE_ID}.json | jq '.[] | select(.jsonPayload.duration_ns != null) | {
  span: .jsonPayload.span_name,
  duration_ms: (.jsonPayload.duration_ns / 1000000)
}'

# View request timeline
cat session_exports/session_${TRACE_ID}.json | jq '.[] | {
  timestamp,
  event: (.jsonPayload.span_name // .jsonPayload.message)
}'

# Find frontend events in session
cat session_exports/session_${TRACE_ID}.json | jq '.[] | select(.jsonPayload.source == "frontend")'
```

**Prerequisites**:

- gcloud CLI installed and authenticated
- `GCP_PROJECT_ID` environment variable set (or in `.env` file)
- `roles/logging.viewer` IAM role for your GCP user
- jq installed for JSON analysis (`brew install jq`)

**Detailed Documentation**:

See [Session Export Guide](../../../docs/development/telemetry-cloud-logging/SESSION_EXPORT_GUIDE.md) for comprehensive usage instructions, troubleshooting, and advanced workflows.

### Creating Spans

```python
from opentelemetry import trace
from telemetry import configure_telemetry

# Configure telemetry
context = configure_telemetry(backend="console")

# Get a tracer
tracer = trace.get_tracer(__name__)

# Create a span
with tracer.start_as_current_span("my_operation") as span:
    span.set_attribute("operation_type", "data_processing")
    span.set_attribute("record_count", 1000)
    # Your code here
```

### Logging with Trace Context

```python
import logging
from opentelemetry import trace
from telemetry import configure_telemetry

# Configure telemetry (enables logging instrumentation)
context = configure_telemetry(backend="jsonl")

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)

with tracer.start_as_current_span("process_request"):
    # Logs automatically include trace_id and span_id
    logger.info("Processing request")
    logger.warning("Retry attempt 1")
    logger.error("Failed to connect to database")
```

## Version History

### 0.1.0 (2025-11-07)

- Initial release
- Console, JSONL, and Disabled backends
- PII redaction utilities
- Comprehensive test coverage (80%+)
- FastAPI integration ready
- Based on proven Garmin Agents implementation

## License

Internal use only - CliniCraft WebApp project.

## References

### Internal Documentation

- [Telemetry Roadmap](../../../docs/development/telemetry/ROADMAP.md) - Implementation phases
- [Phase 1 Plan](../../../docs/development/telemetry/PHASE_1_plan.md) - Core package development
- [CliniCraft Specification](../../../docs/CLINICRAFT_WEBAPP_GCP_SPECIFICATION.md) - System architecture
- [Troubleshooting Guide](docs/TROUBLESHOOTING.md) - Cloud Logging integration troubleshooting

### External Documentation

- [OpenTelemetry Python SDK](https://opentelemetry-python.readthedocs.io/)
- [FastAPI Middleware](https://fastapi.tiangolo.com/tutorial/middleware/)
- [Python Logging](https://docs.python.org/3/library/logging.html)
