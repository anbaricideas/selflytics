# Garmin Agents Repository - Exploration Summary

**Date**: November 2025
**Repository**: `/Users/bryn/repos/garmin_agents`
**Exploration Scope**: Medium thoroughness with focus on reusable patterns and architecture

## 1. PROJECT STRUCTURE & ORGANIZATION

### Package-Based Architecture
The project uses a **monorepo with workspace coordination** pattern via `uv` (Python package manager):

```
garmin_agents/
├── packages/
│   ├── ai-core/              # Core AI functionality (agents, tools, middleware)
│   └── shared-config/        # Shared configuration, credentials, telemetry
├── services/
│   ├── cli/                  # Command-line interface
│   └── web-app/              # Gradio-based web interface
├── infrastructure/
│   ├── terraform/gcp/        # GCP infrastructure (Firestore, service accounts)
│   ├── docker/               # Docker and compose files
│   └── deployment/
│       ├── huggingface/      # HF Spaces deployment setup
│       └── scripts/          # Deployment automation
├── pyproject.toml            # Root workspace manifest
└── requirements.txt          # Exported dependencies
```

### Package Purposes

| Package | Purpose | Key Exports |
|---------|---------|------------|
| **ai-core** | Agent, tools, middleware, Garmin connector | `create_activity_agent()`, `GarminClient`, `LLMMiddleware` |
| **shared-config** | Credentials, telemetry, configuration | `CredentialManager`, `configure_telemetry()`, `redact_for_logging()` |
| **cli** | Click-based CLI for auth, activities, chat | Entry point: `garmin-agents` |
| **web-app** | Gradio web UI with multi-user auth | Entry point: `garmin-web` |

---

## 2. AI AGENT IMPLEMENTATION

### Smolagents Framework Integration

**Library**: `smolagents[litellm,telemetry]` (v0.3+)
**Agent Type**: `ToolCallingAgent` with incremental tool additions

#### Core Agent Setup
```python
# Location: packages/ai-core/src/garmin_ai_core/agents/activity_agent.py

def create_activity_agent(
    tools: list[Tool] | None = None,
    model_spec: str = "ollama:qwen2:7b",
    custom_system_prompt: str | None = None,
    user_context: dict[str, Any] | None = None
) -> ToolCallingAgent:
    """
    Creates ToolCallingAgent with:
    - Pluggable tool list (default, empty, or custom)
    - Model selection via provider:model format
    - Thread-local user context for multi-user support
    - Automatic caching/rate-limiting via middleware
    """
```

#### Default Tools
- `get_recent_activities()` - Fetch Garmin activity data with filters
- `get_user_profile()` - User biometric data (height, weight, VO2 max)
- `get_steps_data()` - Daily step counts
- `get_device_data()` - Device information

#### Tool Implementation Pattern
Tools use `@tool` decorator from smolagents with wrapper functions:

```python
@tool  # type: ignore[misc]
def get_recent_activities(
    start: int = 0,
    limit: int = 20,
    activity_type: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> list[dict[str, Any]] | None:
    """Tool docstring used by agent to understand capabilities."""
    # Call implementation tool
    # Handle GarminAuthRequired exception
    # Log errors with redaction
    # Return None on failure for graceful degradation
```

### Model Specification System

**Format**: `"provider:model"`
**Examples**:
- `"ollama:qwen2:7b"` - Local Ollama
- `"hf:meta-llama/Llama-3.2-3B-Instruct"` - HuggingFace
- `"anthropic:claude-3-5-sonnet"` - Claude (via litellm)

Resolution order (CLI args → ENV var → default):
```python
def resolve_model_spec(cli_model: str | None) -> str:
    if cli_model and cli_model.strip():
        return cli_model
    env_model = os.getenv("CHAT_AGENT_MODEL")
    if env_model:
        return env_model
    return "ollama:qwen2:7b"  # Default fallback
```

### Multi-User Context

User context is passed via thread-local storage:
```python
current_thread = threading.current_thread()
current_thread.user_context = {
    "user_id": 123,  # For Firestore
    "username": "user@example.com"  # For SQLite
}
```

This enables:
- Per-user credential storage via `CredentialManager`
- Per-user token isolation in `GarminClient`
- Per-user Garmin Connect data access

---

## 3. GARMIN DATA INTEGRATION

### Garth Library Integration

**Library**: `garth>=0.4.0` (MFA-enabled Garmin API client)

#### GarminClient Architecture
```python
# Location: packages/ai-core/src/garmin_ai_core/connectors/garmin_client.py

class GarminClient:
    def __init__(self, user_id: int | str | None = None, username: str | None = None):
        self.credential_manager = CredentialManager(user_id, username)
        self.garth_client = garth.Client()  # Per-user instance
        self.authenticated = False

    def authenticate(self, username: str, password: str, raise_on_mfa: bool = False) -> bool:
        """
        - Try resume from stored tokens first
        - Handle MFA: raise (web) vs interactive prompt (CLI)
        - Save tokens to per-user storage
        - Test connection with robust endpoint fallbacks
        """
```

#### Data Retrieval Pattern

**Activity Data**:
- Endpoint: `/activity/search/activities`
- Fields: `activityId`, `activityName`, `activityType`, `startTimeLocal`, `distance`, `duration`, `calories`, `averageHR`, `maxHR`, `steps`, etc.
- Filters: `start` (pagination), `limit` (max 100), `activity_type`, `start_date`, `end_date`
- Field filtering: `SUMMARY_FIELDS`, `STANDARD_ADDITIONAL_FIELDS`, `VERBOSE_FIELDS_TO_REMOVE`

**User Profile Data** (Pydantic models):
- `UserInfo`: Birth date, gender, email, locale, timezone, age
- `BiometricProfile`: Height, weight, VO2 max (running/cycling)
- `DeviceInfo`: Device list with serial numbers, models

**Health Data**:
- Steps: Daily/weekly aggregation
- Heart rate trends
- Sleep data
- Wellness metrics

#### Token Management
- Tokens stored per-user in `~/.garmin_tokens/` or Firestore
- Resume from stored tokens to avoid re-authentication
- Credential storage via keyring (encrypted) or Firestore
- MFA tokens handled securely

#### Error Handling Hierarchy
```python
GarminAuthException (base)
├── GarminAuthRequired      # Need to authenticate
├── GarminMFARequired       # MFA challenge with context
├── GarminInvalidCredentials # Bad credentials (generic message)
├── GarminNetworkError      # Connection/timeout issues
└── GarminValidationError   # Input validation failures
```

---

## 4. FRONTEND - GRADIO WEB INTERFACE

### Structure
**Entry Point**: `services/web-app/src/garmin_web/app.py` → `main()`
**Framework**: Gradio 5.45.0 with FastAPI backend
**Deployment**: HuggingFace Spaces (production URL in `README.md`)

### Key Components

#### Authentication System (Multi-User)
```
services/web-app/src/garmin_web/
├── auth/
│   ├── authentication.py          # Login/register logic
│   ├── user_agent_manager.py      # Per-user agent lifecycle
│   ├── gradio_auth.py             # Gradio auth middleware
│   └── garmin_auth_service.py     # Garmin credential handling
```

**Features**:
- Multi-user login with session tokens
- Per-user Garmin authentication (MFA support)
- User-scoped agent instances
- Session management with persistence

#### UI Components
```python
# Location: services/web-app/src/garmin_web/interface/components.py

create_header()        # Branding: "🏃‍♂️ Garmin AI Coach"
create_chat_section()  # Chat interface with history
create_auth_section()  # Login/MFA forms
create_sidebar()       # Quick actions, tips, status
create_footer()        # Links and attribution
```

#### Chat Handler Pattern
```python
# In app.py:

def user_aware_chat(message: str, history: list, session_token: str) -> tuple:
    """
    - Authenticate user by session token
    - Get/create user's agent instance
    - Call agent.chat_with_tools(message)
    - Handle GarminAuthRequired → show auth form
    - Telemetry: automatic trace correlation
    """
```

#### Workers (Async Processing)
```
services/web-app/src/garmin_web/workers/
├── chat_worker.py    # Background chat processing
└── functions.py      # Utility functions
```

#### Data Layer
```
services/web-app/src/garmin_web/data/
├── database_factory.py    # Firestore/SQLite switching
└── models.py              # Data models
```

#### API Endpoints
```
services/web-app/src/garmin_web/api/
└── telemetry.py           # Telemetry data retrieval endpoint
```

### Gradio-Specific Details
- **SDK Version**: 5.45.0
- **App File**: `services/web-app/src/garmin_web/app.py::main()`
- **Entry Point Command**: `garmin-web` (from `pyproject.toml`)
- **Features Used**: Chatbot interface, blocks layout, authentication

---

## 5. DEPLOYMENT & GCP INFRASTRUCTURE

### GCP Resources (Terraform)
**Location**: `infrastructure/terraform/gcp/main.tf`

Manages:
```hcl
resource "google_firestore_database" "database"
  # Native mode Firestore database
  # Multi-region backup enabled

resource "google_service_account" "firestore_sa"
  # Service account for Firestore access
  # Role: datastore.user
  # Key: manual creation (org policy constraint)
```

### HuggingFace Spaces Deployment
**Production URL**: https://huggingface.co/spaces/bjpromptly/garmin-agent

**Deployment Process**:
```bash
./infrastructure/deployment/scripts/deploy-to-hf.sh -y
# 1. Generate requirements.txt from uv.lock
# 2. Copy packages/, services/, app.py
# 3. Push to HF git repo (triggers rebuild)
```

**Prerequisites**:
- `.env` with `HF_USERNAME`, `HF_SPACE_NAME`, `HUGGINGFACE_HUB_TOKEN`
- GCP service account key (for Firestore access)
- `requirements.txt` for dependencies

**Deployment Artifacts**:
- `infrastructure/deployment/huggingface/README.md` - Full guide
- `infrastructure/deployment/huggingface/.spacesconfig.yaml` - HF config
- `infrastructure/deployment/huggingface/app.py` - Entry point wrapper

### Docker Support
```
infrastructure/docker/
├── Dockerfile              # Multi-stage build
├── docker-compose.yml      # Main compose (app + services)
├── docker-compose.gcs-emulator.yml      # GCS testing
└── docker-compose.firestore-emulator.yml # Firestore testing
```

---

## 6. KEY DEPENDENCIES & TECHNOLOGIES

### Core Dependencies

| Library | Version | Purpose |
|---------|---------|---------|
| **smolagents** | 0.3+ | AI agent framework |
| **garth** | 0.4+ | Garmin API client (MFA support) |
| **gradio** | 5.45.0 | Web UI framework |
| **pydantic** | 2.0+ | Data validation |
| **fastapi** | (via gradio) | Web framework |
| **opentelemetry-sdk** | 0.41b+ | Observability/tracing |
| **google-cloud-firestore** | 1.8.1+ | Database (production) |
| **google-cloud-storage** | 3.4.1+ | Log export (HF Spaces) |
| **litellm** | (via smolagents) | Multi-LLM provider support |
| **diskcache** | 5.6.3+ | Disk-based caching |
| **aiolimiter** | 1.2.1+ | Rate limiting |
| **cachetools** | 6.2.0+ | In-memory caching |
| **click** | 8.0+ | CLI framework |
| **python-dotenv** | 1.0+ | Environment config |
| **keyring** | 24.0+ | Credential storage |
| **cryptography** | 41.0+ | Password encryption |
| **rich** | 13.0+ | CLI formatting |

### Development Tools
- **uv**: Package manager (ONLY, never pip)
- **pytest**: Testing framework with plugins (xdist, asyncio, mock, cov)
- **mypy**: Type checking (required)
- **ruff**: Linting/formatting
- **pre-commit**: Git hooks
- **playwright**: E2E browser testing

---

## 7. DATA FLOW ARCHITECTURE

### End-to-End Flow: Garmin → Agent → User

```
┌─────────────────────────────────────────────────────────────┐
│                    USER INTERACTION                         │
│  (CLI: `garmin-agents chat` or Web: Gradio chatbot)        │
└──────────────────────┬──────────────────────────────────────┘
                       │
         ┌─────────────▼──────────────────┐
         │  1. USER MESSAGE               │
         │  (Natural language query)      │
         └─────────────┬──────────────────┘
                       │
         ┌─────────────▼──────────────────────────────────────┐
         │  2. ACTIVITY AGENT (smolagents ToolCallingAgent)  │
         │  - Parse user intent                              │
         │  - Decide which tools to call                     │
         │  - Format tool arguments                          │
         └─────────────┬──────────────────────────────────────┘
                       │
         ┌─────────────▼──────────────────────────────────────┐
         │  3. TOOL CALLING LAYER                            │
         │  - @tool decorated functions                      │
         │  - get_recent_activities()                        │
         │  - get_user_profile()                             │
         │  - get_steps_data()                               │
         └─────────────┬──────────────────────────────────────┘
                       │
         ┌─────────────▼──────────────────────────────────────┐
         │  4. LLM MIDDLEWARE                                │
         │  - Caching (disk/memory, 7-day TTL)               │
         │  - Rate limiting (per-provider)                   │
         │  - Circuit breaker                                │
         │  - Automatic telemetry spans                      │
         └─────────────┬──────────────────────────────────────┘
                       │
         ┌─────────────▼──────────────────────────────────────┐
         │  5. GARMIN CLIENT                                 │
         │  - Thread-local per-user instance                 │
         │  - Token resumption                               │
         │  - MFA handling                                   │
         │  - Error mapping (GarminAuthException)            │
         └─────────────┬──────────────────────────────────────┘
                       │
         ┌─────────────▼──────────────────────────────────────┐
         │  6. GARTH LIBRARY                                 │
         │  - HTTP requests to Garmin API                    │
         │  - Session management                             │
         │  - Response parsing                               │
         └─────────────┬──────────────────────────────────────┘
                       │
         ┌─────────────▼──────────────────────────────────────┐
         │  7. GARMIN CONNECT API                            │
         │  - /activity/search/activities                    │
         │  - /userprofile-service/userprofile              │
         │  - /wellness-service/wellness/{date}              │
         └─────────────┬──────────────────────────────────────┘
                       │
         ┌─────────────▼──────────────────────────────────────┐
         │  8. RESPONSE PROCESSING                           │
         │  - Parse Garmin API response                      │
         │  - Validate with Pydantic models                  │
         │  - Format for agent consumption                   │
         │  - Filter fields (summary/verbose)                │
         └─────────────┬──────────────────────────────────────┘
                       │
         ┌─────────────▼──────────────────────────────────────┐
         │  9. AGENT REASONING                               │
         │  - Synthesize data into response                  │
         │  - Answer user question                           │
         │  - Provide fitness insights                       │
         │  - Call additional tools if needed                │
         └─────────────┬──────────────────────────────────────┘
                       │
         ┌─────────────▼──────────────────────────────────────┐
         │  10. TELEMETRY CAPTURE                            │
         │  - OpenTelemetry spans                            │
         │  - Python logs with trace context                 │
         │  - Export to JSONL/Firestore/GCS                  │
         └─────────────┬──────────────────────────────────────┘
                       │
         ┌─────────────▼──────────────────────────────────────┐
         │  11. USER RESPONSE                                │
         │  - Display agent reply                            │
         │  - Show formatting (markdown)                     │
         │  - Persist in chat history                        │
         └─────────────────────────────────────────────────────┘
```

### Key Design Patterns

**1. Dependency Injection**
- `GarminClient` with optional user context
- `ToolCallingAgent` with pluggable tools
- Middleware backends (disk/memory cache)

**2. Exception-Based Flow Control**
- `GarminAuthRequired` triggers auth UI
- `GarminMFARequired` with context dict
- Graceful degradation (return `None`)

**3. Thread-Local User Context**
- Each request/thread gets isolated user data
- Multi-user support without global state
- Thread-safe credential/token access

**4. Middleware Interception**
- LLM calls automatically cached
- Rate limiting transparent to agent
- Spans created automatically

**5. Redaction for Security**
- All external API errors redacted
- User PII redacted in logs
- `redact_for_logging()` utility function
- Pre-commit hooks check for f-string violations

---

## 8. UNIFIED TELEMETRY SYSTEM

### Telemetry Architecture

**Location**: `packages/shared-config/src/garmin_shared_config/config/telemetry.py`

**Flow**:
1. **Python Logging** + **OpenTelemetry Spans** → Single capture
2. **Automatic Trace Context Injection** - logs within spans get `trace_id`, `span_id`
3. **Backend Selection** - environment-driven:

| Backend | Export Destination | Use Case |
|---------|-------------------|----------|
| **console** | stdout | Local debugging |
| **jsonl** | `./logs/session_*.jsonl` | Local development |
| **otlp** | OpenTelemetry Protocol endpoint (Langfuse, etc.) | Third-party integration |
| **gcs** | Google Cloud Storage | HuggingFace Spaces production |
| **firestore** | Cloud Firestore | Multi-user data persistence |
| **disabled** | (none) | Minimal mode |

**Configuration**:
```python
configure_telemetry(backend=TelemetryBackend, ...)
# Auto-initializes LoggerProvider + TracerProvider
# Instruments: logging, smolagents, OpenInference
```

### Trace Context Injection

Spans created by `smolagents` are automatically correlated with Python logs:
```python
# During agent.chat_with_tools():
with tracer.start_as_current_span("agent_chat") as span:
    logger.info("User message: %s", message)
    # → Log automatically includes span_id, trace_id
```

### Security: Automatic Redaction

Rules (from `CLAUDE.md`):
- **REDACT**: Usernames, PII, tokens, external API errors
- **NOT REDACT**: Internal Python exceptions

```python
# ✅ Correct
logger.error("Garmin API error: %s", redact_for_logging(str(e)))
logger.info("User %s logged in", redact_for_logging(username))

# ❌ Wrong
logger.error(f"API error: {error}")  # f-strings bypass redaction
```

---

## 9. REUSABLE PATTERNS & TEMPLATES

### Pattern 1: Tool Implementation
```python
@tool
def my_tool(param: str) -> dict | None:
    """Docstring for agent understanding."""
    try:
        result = _implementation(param)
        return result
    except GarminAuthRequired:
        logger.info("Auth required for my_tool")
        raise
    except Exception as e:
        logger.error("my_tool error: %s", redact_for_logging(str(e)))
        return None
```

### Pattern 2: User-Aware Data Retrieval
```python
def _get_user_aware_garmin_client() -> GarminClient:
    current_thread = threading.current_thread()
    if hasattr(current_thread, "user_context") and current_thread.user_context:
        user_id = current_thread.user_context.get("user_id")
        username = current_thread.user_context.get("username")
        return GarminClient(user_id=user_id, username=username)
    return GarminClient()  # Legacy mode
```

### Pattern 3: Multi-User Middleware
```python
# In agent creation:
create_activity_agent(
    user_context={"user_id": 123, "username": "user@example.com"}
)

# Sets thread-local:
current_thread.user_context = {...}
```

### Pattern 4: Authentication Flow (Web)
```python
# 1. Try chat
try:
    response = agent.chat_with_tools(message)
except GarminAuthRequired:
    # 2. Show auth form
    return show_garmin_auth_form()
except GarminMFARequired as e:
    # 3. Show MFA form
    return show_mfa_form(e.mfa_context)
```

### Pattern 5: Error Handling Hierarchy
```python
try:
    client.authenticate(username, password, raise_on_mfa=True)
except GarminMFARequired as e:
    # Handle MFA with context
except GarminInvalidCredentials:
    # Show generic error (no username enumeration)
except GarminNetworkError:
    # Retry or show connectivity error
except GarminValidationError:
    # Show input validation error
```

### Pattern 6: Pydantic Data Models
```python
from pydantic import BaseModel, Field

class UserProfile(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_default=True,
    )

    birth_date: date = Field(alias="birthDate")
    vo2_max: float | None = Field(default=None, alias="vo2Max")

    def model_dump(self, by_alias=False, exclude_none=True, mode="json"):
        # For agent consumption
```

### Pattern 7: Middleware Configuration
```python
from garmin_ai_core.middleware import LLMMiddleware, MiddlewareConfig

config = MiddlewareConfig(
    cache_enabled=True,
    cache_backend="disk",  # or "memory"
    cache_ttl_seconds=604800,  # 7 days
    cache_empty_responses=False,
)
middleware = LLMMiddleware(config=config)
```

---

## 10. DEVELOPMENT WORKFLOW & CONSTRAINTS

### Critical Constraints (from `CLAUDE.md`)
- **Package Manager**: ONLY `uv` (`uv sync --extra all`), never pip
- **Type Hints**: Required for all code (MyPy enforced)
- **Line Length**: 100 characters max
- **Async Testing**: Use anyio, not asyncio
- **Logging Security**: Redaction + formatting rules (no f-strings in logger calls)
- **Pre-commit**: All hooks must pass

### Test Validation Protocol
Before claiming "all tests pass", verify ALL:
```bash
# 1. Full workspace tests
uv run pytest --tb=short

# 2. CI simulation (sequential)
uv run pytest -m "not llm and not local_only..." --timeout=180 --tb=short

# 3. CI simulation (parallel)
uv run pytest -m "not llm and not local_only..." -n auto --timeout=180

# 4. Pre-commit hooks
uv run pre-commit run --all-files

# 5. Check actual CI status (required before merge)
gh pr checks <PR_NUMBER>
```

### Code Organization
- **Imports**: All at file top (PEP 8)
- **Composition over Inheritance**: For complex objects
- **Docstrings**: Required for public functions/classes
- **Type Aliases**: `DateInput = str | date | datetime`
- **Async Patterns**: Use context managers, type async/await correctly

---

## SUMMARY: KEY TAKEAWAYS FOR REUSE

### What Makes This Project Reusable

1. **Modular Package Structure** - Each package is independently installable
2. **Pluggable Architecture** - Tools, models, middleware, backends are all injectable
3. **Clear Abstraction Layers** - Agent → Tools → Client → API
4. **Security by Default** - Redaction, encryption, MFA built-in
5. **Observability First** - Unified telemetry with trace correlation
6. **Multi-User Ready** - Thread-local context, per-user credentials
7. **Production-Grade Patterns** - Middleware, caching, rate limiting, circuit breaker
8. **Comprehensive Testing** - Unit, integration, E2E, behavioral test support
9. **Type-Safe** - Full mypy coverage, Pydantic validation
10. **Well-Documented** - Docstrings, CLAUDE.md, architecture docs

### Patterns Worth Adopting

1. **Smolagents + Custom Tools** - Simple agent setup with controlled capabilities
2. **Exception-Based Flow Control** - Exceptions as navigation mechanism
3. **Middleware Interception** - Transparent caching/limiting without agent changes
4. **Unified Telemetry** - Single system for logs + traces + spans
5. **Pydantic Models** - Type-safe, validated data structures
6. **Thread-Local Context** - Safe multi-user support
7. **Redaction Utilities** - Security-first logging
8. **uv Monorepo** - Package coordination with clean separation
