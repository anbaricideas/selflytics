# Reusable Patterns from Garmin Agents - Quick Reference

This guide highlights the most valuable patterns from `garmin_agents` that can be directly adopted in new projects.

---

## 1. SMOLAGENTS + CUSTOM TOOLS PATTERN

### Problem It Solves
- Need to create an AI agent with controlled, specific capabilities
- Don't want the agent to have unrestricted tool access
- Need to integrate with existing data sources

### Pattern Implementation

**Step 1: Define Your Tools**
```python
# tools/my_tools.py
from smolagents import tool

@tool  # type: ignore[misc]
def fetch_user_data(user_id: int) -> dict | None:
    """Retrieve user profile from database.

    This docstring helps the agent understand when to use this tool.
    The agent will read this to decide if it's relevant to the user's query.
    """
    try:
        result = _implementation_fetch_user(user_id)
        return result
    except AuthError:
        logger.info("Auth error in fetch_user_data")
        raise
    except Exception as e:
        logger.error("Error: %s", redact_for_logging(str(e)))
        return None  # Graceful degradation

@tool
def send_notification(user_id: int, message: str) -> bool:
    """Send a notification to the user."""
    # Similar pattern...
```

**Step 2: Create Agent Factory**
```python
# agents/my_agent.py
from smolagents import ToolCallingAgent

def create_my_agent(
    tools: list[Tool] | None = None,
    model_spec: str = "ollama:qwen2:7b",
    custom_system_prompt: str | None = None,
) -> ToolCallingAgent:
    """Factory function for easy agent creation."""

    if tools is None:
        tools = get_default_tools()

    model = create_model_from_spec(model_spec)

    agent = ToolCallingAgent(
        model=model,
        tools=tools,
        system_prompt=custom_system_prompt or DEFAULT_SYSTEM_PROMPT,
    )
    return agent

def get_default_tools() -> list[Tool]:
    return [
        fetch_user_data,
        send_notification,
    ]
```

**Step 3: Use in Your Application**
```python
# Basic usage
agent = create_my_agent()
response = agent.chat_with_tools("What's my profile?")

# Custom tools for testing
test_agent = create_my_agent(tools=[])  # No tools for unit testing

# Custom model
agent = create_my_agent(model_spec="hf:meta-llama/Llama-3.2-3B-Instruct")
```

### Why This Works
- Tools are pluggable (testable, flexible)
- Tool docstrings guide agent behavior automatically
- Agent decides when to call tools based on user intent
- Easy to add/remove capabilities
- Factory pattern allows configuration via environment or parameters

---

## 2. EXCEPTION-BASED FLOW CONTROL

### Problem It Solves
- Complex authentication flows (MFA, OAuth challenges)
- Switching UI states based on agent behavior (show form vs. chat)
- Clean error boundaries without passing status codes everywhere

### Pattern Implementation

**Step 1: Define Exception Hierarchy**
```python
# exceptions.py
class AppException(Exception):
    """Base exception for application."""
    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}

class AuthRequired(AppException):
    """Raised when authentication is needed."""
    pass

class MFARequired(AppException):
    """Raised when MFA code is needed."""
    def __init__(self, message: str, mfa_context: dict):
        super().__init__(message, details={"mfa_context": mfa_context})
        self.mfa_context = mfa_context

class InvalidInput(AppException):
    """User input validation failed."""
    pass
```

**Step 2: Use in Core Logic**
```python
# client.py
class MyClient:
    def authenticate(self, username: str, password: str) -> bool:
        try:
            result = self._login_with_credentials(username, password)
            if result.needs_mfa:
                raise MFARequired(
                    "MFA code required",
                    mfa_context={"mfa_token": result.token, "username": username}
                )
            return True
        except ConnectionError as e:
            raise NetworkError("Could not connect to server") from e

# In tool:
@tool
def my_protected_tool(param: str) -> dict | None:
    try:
        client = get_authenticated_client()
        return client.fetch_data(param)
    except AuthRequired:
        # Tool execution fails, UI catches it
        raise  # Re-raise to trigger auth form
    except Exception as e:
        logger.error("Tool error: %s", redact_for_logging(str(e)))
        return None
```

**Step 3: Handle in UI Layer**
```python
# gradio app
def chat_interface(message: str, session_token: str) -> tuple:
    """Main chat handler with exception-based flow control."""
    try:
        user = authenticate_user(session_token)
        agent = get_user_agent(user)
        response = agent.chat_with_tools(message)
        return response, None  # No form needed

    except AuthRequired:
        return None, show_auth_form()  # Show login form

    except MFARequired as e:
        mfa_context = e.mfa_context
        return None, show_mfa_form(mfa_context)

    except InvalidInput as e:
        return f"Invalid input: {e.message}", None
```

### Why This Works
- Status is implicit in the exception type (no return values to track)
- UI logic is clear and declarative
- Exceptions naturally bubble up to the right handler
- Context (MFA token, etc.) travels with the exception
- No if/else chains for status checking

---

## 3. MIDDLEWARE INTERCEPTION FOR CROSS-CUTTING CONCERNS

### Problem It Solves
- Caching LLM results without changing agent code
- Rate limiting transparently
- Adding observability without explicit instrumentation
- Swapping backends (memory vs. disk cache) at runtime

### Pattern Implementation

**Step 1: Define Middleware Interface**
```python
# middleware/core.py
from dataclasses import dataclass
from typing import Any, Protocol

@dataclass
class LLMResponse:
    content: str
    model: str
    tokens_used: int
    cache_hit: bool = False

class CacheBackend(Protocol):
    """Cache backend interface - allows swapping implementations."""
    def get(self, key: str) -> LLMResponse | None: ...
    def set(self, key: str, value: LLMResponse, ttl: int) -> None: ...
    def delete(self, key: str) -> None: ...

class LLMMiddleware:
    def __init__(
        self,
        cache_backend: CacheBackend | None = None,
        rate_limiter: RateLimiter | None = None,
    ):
        self.cache = cache_backend or DiskCacheBackend()
        self.limiter = rate_limiter or NoOpLimiter()

    def call_model(
        self,
        model: str,
        messages: list[dict],
    ) -> LLMResponse:
        """Intercept all LLM calls."""
        cache_key = generate_cache_key(model, messages)

        # Check cache
        cached = self.cache.get(cache_key)
        if cached:
            logger.debug("Cache hit for %s", cache_key)
            return cached

        # Rate limit
        self.limiter.acquire_token(model)

        # Call model
        response = self._actually_call_model(model, messages)

        # Cache result
        self.cache.set(cache_key, response, ttl=604800)  # 7 days

        return response
```

**Step 2: Swap Cache Backends at Runtime**
```python
# In configuration
def create_middleware(config: MiddlewareConfig) -> LLMMiddleware:
    if config.cache_backend == "disk":
        cache = DiskCacheBackend(cache_dir=config.cache_dir)
    elif config.cache_backend == "memory":
        cache = MemoryCacheBackend(max_size=1000)
    else:
        cache = NoOpCache()

    return LLMMiddleware(cache_backend=cache)

# Usage
config = MiddlewareConfig.from_environment()  # Reads from ENV vars
middleware = create_middleware(config)

# In your agent calls
response = middleware.call_model("gpt-4", messages)
```

**Step 3: Transparent Integration**
```python
# Agent doesn't know about caching - it's transparent
class MyAgent:
    def __init__(self, middleware: LLMMiddleware):
        self.llm = middleware

    def chat(self, message: str) -> str:
        # This automatically uses caching, rate limiting, etc.
        response = self.llm.call_model("gpt-4", [{"role": "user", "content": message}])
        return response.content
```

### Why This Works
- Cross-cutting concerns (caching, limiting) are centralized
- Agent code doesn't change when you add features
- Easy to test with different backends
- Configuration-driven (swap backends via ENV vars)
- Can disable entirely by using NoOp backends

---

## 4. UNIFIED TELEMETRY WITH TRACE CORRELATION

### Problem It Solves
- Python logs and OpenTelemetry spans are separate
- Hard to correlate logs with traces
- Duplicate instrumentation code
- No single place to export observability data

### Pattern Implementation

**Step 1: Configure Telemetry**
```python
# config/telemetry.py
from opentelemetry import trace as trace_api
from opentelemetry.sdk import trace as trace_sdk
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from openinference.instrumentation.smolagents import SmolagentsInstrumentor

def configure_telemetry(backend: str = "jsonl"):
    """One-call setup for all observability."""

    # Create tracer provider
    tracer_provider = trace_sdk.TracerProvider()
    trace_api.set_tracer_provider(tracer_provider)

    # Instrument libraries
    LoggingInstrumentor().instrument()  # Correlate Python logs
    SmolagentsInstrumentor().instrument()  # Instrument agents

    # Configure exporter based on backend
    if backend == "console":
        processor = SimpleSpanProcessor(ConsoleSpanExporter())
    elif backend == "jsonl":
        processor = BatchSpanProcessor(JSONLSpanExporter())
    elif backend == "otlp":
        processor = BatchSpanProcessor(OTLPSpanExporter())

    tracer_provider.add_span_processor(processor)

    return tracer_provider
```

**Step 2: Use in Your Code (No Special Code Needed)**
```python
import logging

logger = logging.getLogger(__name__)
tracer = trace_api.get_tracer(__name__)

def my_function(user_id: int) -> dict:
    with tracer.start_as_current_span("fetch_user") as span:
        span.set_attribute("user_id", user_id)

        logger.info("Fetching user %d", user_id)  # ← Automatically gets span ID!

        # Your code here
        result = fetch_from_db(user_id)

        logger.debug("Result: %s", result)  # ← Also gets span ID!

        return result
```

**Step 3: Query Correlations**
```bash
# View logs with trace IDs
cat logs/session_*.jsonl | jq 'select(.trace_id == "abc123")'

# Find all logs for a specific span
cat logs/session_*.jsonl | jq 'select(.span_id == "xyz789")'

# View all errors from a session
cat logs/session_*.jsonl | jq 'select(.severity == "ERROR")'
```

### Why This Works
- Single instrumentation setup for everything
- All telemetry exported to same place
- Logs and traces are automatically correlated
- Easy to switch backends (no code changes)
- Out-of-the-box integration with smolagents

---

## 5. THREAD-LOCAL CONTEXT FOR MULTI-USER SUPPORT

### Problem It Solves
- Each user needs isolated data (credentials, tokens, preferences)
- Async/concurrent requests from different users
- Avoiding global state while sharing code
- Type-safe user context passing

### Pattern Implementation

**Step 1: Define Context Type**
```python
# context/user_context.py
from typing import TypedDict

class UserContext(TypedDict):
    user_id: int | str
    username: str
    email: str
    preferences: dict

def get_user_context() -> UserContext | None:
    """Get current user context from thread-local storage."""
    thread = threading.current_thread()
    return getattr(thread, "user_context", None)

def set_user_context(context: UserContext) -> None:
    """Set user context for current thread."""
    thread = threading.current_thread()
    thread.user_context = context

def clear_user_context() -> None:
    """Clear user context (use in cleanup)."""
    thread = threading.current_thread()
    if hasattr(thread, "user_context"):
        delattr(thread, "user_context")
```

**Step 2: Use in Your Services**
```python
# services/user_service.py
def get_user_credentials() -> tuple[str, str]:
    """Get current user's credentials (from thread-local)."""
    context = get_user_context()
    if not context:
        raise ValueError("No user context set")

    # Load from per-user storage
    user_id = context["user_id"]
    return credential_manager.load_credentials(user_id)

def fetch_user_data(data_type: str) -> dict:
    """Fetch data for current user."""
    context = get_user_context()
    if not context:
        raise ValueError("No user context set")

    user_id = context["user_id"]
    return api_client.get_user_data(user_id, data_type)
```

**Step 3: Set Context at Request Boundary**
```python
# In web app (Gradio, FastAPI, etc.)
async def handle_user_request(
    message: str,
    session_token: str,
) -> str:
    """Main request handler - set context at boundary."""

    # Authenticate request
    user = authenticate_by_token(session_token)

    # Set context for this request/thread
    set_user_context({
        "user_id": user.id,
        "username": user.username,
        "email": user.email,
        "preferences": user.preferences,
    })

    try:
        # All subsequent code can access user context
        agent = create_agent()  # Uses context internally
        response = agent.chat(message)  # Uses context for tools
        return response
    finally:
        # Always cleanup
        clear_user_context()
```

**Step 4: Use in Agent Tools**
```python
@tool
def get_my_activities() -> list[dict] | None:
    """Get activities for current user (from thread context)."""
    context = get_user_context()
    if not context:
        raise ValueError("User not authenticated")

    user_id = context["user_id"]
    return fetch_activities(user_id)
```

### Why This Works
- No global state (clean architecture)
- Each request has isolated context
- Works with threading and async patterns
- Type-safe with TypedDict
- Automatic cleanup with try/finally
- Credentials never passed through function signatures

---

## 6. PYDANTIC MODELS FOR DATA VALIDATION

### Problem It Solves
- Validating external API responses
- Type hints at runtime
- Auto-generating API schemas
- Flexible serialization (JSON, dict, etc.)

### Pattern Implementation

**Step 1: Define Models**
```python
# models/activity.py
from pydantic import BaseModel, Field, ConfigDict

class Activity(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_default=True,
    )

    activity_id: int = Field(alias="activityId")
    activity_name: str = Field(alias="activityName")
    activity_type: str = Field(alias="activityType")
    distance: float  # meters
    duration: int    # seconds
    calories: int | None = None
    average_hr: int | None = Field(default=None, alias="averageHR")

    # Computed properties
    @property
    def duration_minutes(self) -> float:
        return self.duration / 60

class UserProfile(BaseModel):
    user_id: int = Field(alias="userId")
    email: str
    birth_date: date = Field(alias="birthDate")
    height: float  # cm
    weight: float  # grams
    vo2_max: float | None = Field(default=None, alias="vo2Max")
```

**Step 2: Validate External Data**
```python
# connectors/api_client.py
import requests

def fetch_activities(user_id: int) -> list[Activity]:
    """Fetch and validate activities from API."""

    response = requests.get(
        f"https://api.example.com/activities",
        params={"userId": user_id},
    )
    response.raise_for_status()

    raw_data = response.json()

    # Validate with Pydantic
    # This raises ValidationError if data doesn't match schema
    activities = [Activity(**item) for item in raw_data]

    return activities
```

**Step 3: Serialize for Different Contexts**
```python
# For agent consumption (JSON-safe, no None values)
activity.model_dump(
    by_alias=False,
    exclude_none=True,
    mode="json",
)

# For API response
activity.model_dump_json()

# For database storage
activity.model_dump(by_alias=True)

# For debugging (includes type info)
activity.model_dump(mode="python")
```

**Step 4: Custom Validation**
```python
from pydantic import field_validator

class Activity(BaseModel):
    activity_type: str
    distance: float

    @field_validator("activity_type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        """Normalize activity type."""
        valid_types = {"running", "cycling", "swimming"}
        if v.lower() not in valid_types:
            raise ValueError(f"Unknown activity type: {v}")
        return v.lower()

    @field_validator("distance")
    @classmethod
    def validate_distance(cls, v: float) -> float:
        """Distance must be positive."""
        if v < 0:
            raise ValueError("Distance cannot be negative")
        return v
```

### Why This Works
- Runtime type checking (catch API changes early)
- Self-documenting data models
- Automatic validation (no manual checks)
- Flexible serialization (one model, many outputs)
- Works seamlessly with OpenAPI/JSON schemas

---

## 7. SECURE LOGGING WITH REDACTION

### Problem It Solves
- Prevent accidental exposure of passwords, tokens, PII in logs
- Still capture useful debugging information
- Comply with privacy regulations (GDPR, CCPA)
- Automated enforcement via pre-commit hooks

### Pattern Implementation

**Step 1: Create Redaction Utility**
```python
# logging_utils.py
import re

def redact_for_logging(value: str | None) -> str:
    """
    Redact sensitive strings for logging.
    Shows first and last character(s) with asterisks.

    Examples:
        "password123" → "p*********3"
        "a" → "a"
        "ab" → "a*b"
        None → "(redacted)"
    """
    if value is None or value == "":
        return "(redacted)"

    value_str = str(value)

    if len(value_str) <= 2:
        return value_str

    first = value_str[0]
    last = value_str[-1]
    middle = "*" * (len(value_str) - 2)

    return f"{first}{middle}{last}"

def redact_string(value: str | None) -> str:
    """Alias for redact_for_logging."""
    return redact_for_logging(value)
```

**Step 2: Use in Code**
```python
# ✅ CORRECT - External errors (may contain user data)
logger.error("Garmin API error: %s", redact_for_logging(str(e)))

# ✅ CORRECT - PII and secrets
logger.info("User %s authenticated", redact_for_logging(username))
logger.debug("Token: %s", redact_for_logging(token))

# ✅ CORRECT - Use % formatting (not f-strings)
logger.error("Failed for user %s", redact_for_logging(user_email))

# ❌ WRONG - f-strings bypass redaction
logger.error(f"Error: {error}")  # Unchecked content

# ❌ WRONG - Forgetting to redact external data
logger.error("API error: %s", str(e))  # Could leak PII
```

**Step 3: Pre-commit Hook Enforcement**
```yaml
# .pre-commit-config.yaml
- repo: local
  hooks:
    - id: check-logger-f-strings
      name: Check for f-strings in logger calls
      entry: bash -c 'grep -r "logger\.\(info\|debug\|warning\|error\).*f[\"'\'']" --include="*.py" . && exit 1 || exit 0'
      language: system
      types: [python]
```

### Why This Works
- Centralized redaction logic (DRY)
- Pre-commit hooks prevent accidental leaks
- Clear audit trail of what was redacted
- Easy to enhance (add more patterns)
- Compliant with privacy regulations

---

## 8. FACTORY PATTERN WITH CONFIGURATION

### Problem It Solves
- Creating complex objects with many options
- Swapping implementations at runtime
- Configuration from environment variables
- Testing with different backends

### Pattern Implementation

**Step 1: Define Configuration**
```python
# config.py
from dataclasses import dataclass
import os

@dataclass
class AppConfig:
    """Application configuration."""

    # Database
    db_backend: str = os.getenv("DB_BACKEND", "sqlite")
    db_path: str = os.getenv("DB_PATH", "./data.db")

    # Cache
    cache_enabled: bool = os.getenv("CACHE_ENABLED", "true").lower() == "true"
    cache_backend: str = os.getenv("CACHE_BACKEND", "disk")
    cache_dir: str = os.getenv("CACHE_DIR", ".cache")

    # Model
    model_provider: str = os.getenv("MODEL_PROVIDER", "ollama")
    model_name: str = os.getenv("MODEL_NAME", "qwen2:7b")

    @classmethod
    def from_environment(cls) -> "AppConfig":
        """Create config from environment variables."""
        return cls()
```

**Step 2: Create Factories**
```python
# factories.py
def create_database(config: AppConfig) -> Database:
    """Factory for database creation."""
    if config.db_backend == "sqlite":
        return SQLiteDatabase(config.db_path)
    elif config.db_backend == "firestore":
        return FirestoreDatabase()
    else:
        raise ValueError(f"Unknown backend: {config.db_backend}")

def create_cache(config: AppConfig) -> CacheBackend:
    """Factory for cache backend."""
    if not config.cache_enabled:
        return NoOpCache()

    if config.cache_backend == "disk":
        return DiskCache(config.cache_dir)
    elif config.cache_backend == "memory":
        return MemoryCache()
    else:
        raise ValueError(f"Unknown cache: {config.cache_backend}")

def create_model(config: AppConfig) -> LanguageModel:
    """Factory for LLM model."""
    spec = f"{config.model_provider}:{config.model_name}"
    return create_model_from_spec(spec)

def create_app(config: AppConfig | None = None) -> App:
    """Main application factory."""
    config = config or AppConfig.from_environment()

    database = create_database(config)
    cache = create_cache(config)
    model = create_model(config)

    return App(
        database=database,
        cache=cache,
        model=model,
    )
```

**Step 3: Use in Application**
```python
# main.py
def main():
    # Create from environment
    app = create_app()

    # Or with custom config
    config = AppConfig(
        db_backend="firestore",
        cache_backend="memory",
    )
    app = create_app(config)

    # Run
    app.run()

# In tests
def test_my_feature():
    config = AppConfig(
        db_backend="sqlite",
        cache_enabled=False,
        model_name="test-model",
    )
    app = create_app(config)
    # Test with mocked backends
```

### Why This Works
- Single responsibility (each factory creates one thing)
- Configuration externalized (no magic strings)
- Easy to test (swap backends)
- Easy to extend (add new backends)
- Clear factory interface

---

## SUMMARY: Patterns to Adopt

| Pattern | When to Use | Key Benefit |
|---------|------------|------------|
| **Smolagents + Tools** | Building AI agents | Controlled capabilities, testable |
| **Exception-Based Flow** | Complex state transitions | Clean, declarative code |
| **Middleware Interception** | Cross-cutting concerns (caching, logging) | Transparent, pluggable |
| **Unified Telemetry** | Observability and debugging | Correlated logs + traces |
| **Thread-Local Context** | Multi-user/multi-tenant | Safe, clean isolation |
| **Pydantic Models** | External data validation | Type-safe, self-documenting |
| **Redaction Utilities** | Security-conscious logging | Compliance, leak prevention |
| **Factory Pattern** | Complex object creation | Testable, configurable |

All of these patterns work together to create a **production-ready, extensible, type-safe system** that's easy to test and maintain.
