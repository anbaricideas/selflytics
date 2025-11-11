# Selflytics - Project Specification

**Version:** 1.0
**Date:** 2025-11-11
**Status:** Draft for Review

---

## Executive Summary

Selflytics is a multi-user SaaS application that provides AI-powered analysis and insights for quantified self data from wearable devices. The initial version focuses on Garmin ecosystem integration with natural language chat interface augmented by AI-generated visualizations.

**Core Value Proposition:**
- Natural language interface for exploring personal fitness data
- AI-driven trend forecasting and personalized insights
- Visual analysis generated on-demand in response to user queries
- Secure, privacy-focused personal health data management

**Technology Foundation:**
- Reuses proven infrastructure from CliniCraft (Pydantic-AI, FastAPI, Cloud Run, Terraform, Cloud Logging telemetry)
- Reuses Garmin integration patterns from Garmin Agents (garth library, token management)
- Modern progressive-enhancement frontend (Jinja2 + HTMX + Alpine.js + TailwindCSS)
- Well-structured monorepo from day one (follows CliniCraft folder organization)

---

## 1. Project Vision & Goals

### 1.1 Primary Goals

1. **Accessible AI Analysis**: Enable non-technical users to gain insights from fitness data through natural conversation
2. **Visual Intelligence**: Generate contextual charts and visualizations in response to user queries
3. **Privacy-First**: Keep user health data secure with transparent data handling
4. **Extensible Architecture**: Design for future expansion to multiple data sources (Fitbit, Apple Health, manual uploads)

### 1.2 Non-Goals (Out of Scope for MVP)

- Multiple wearable integrations (Garmin only initially)
- Mobile native apps (web-first, responsive design only)
- Real-time data syncing (periodic refresh acceptable)
- Social features or data sharing between users
- Medical-grade diagnostics or health advice

### 1.3 Success Criteria

- Users can authenticate, link Garmin account, and query their data within 5 minutes
- Chat interface responds with relevant insights in under 10 seconds
- AI-generated visualizations accurately reflect requested data
- 80%+ test coverage maintained throughout development
- Infrastructure costs under $50/month for 100 active users

---

## 2. Technical Architecture

### 2.1 System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Browser                             │
│  (Jinja2 + HTMX + Alpine.js + TailwindCSS)                      │
└───────────────────────────┬─────────────────────────────────────┘
                            │ HTTPS
┌───────────────────────────▼─────────────────────────────────────┐
│                    Cloud Run (FastAPI)                           │
│  ┌────────────────┐  ┌──────────────────┐  ┌─────────────────┐ │
│  │  Auth Service  │  │  Chat Service    │  │  Garmin Service │ │
│  │  (JWT + bcrypt)│  │  (Pydantic-AI)   │  │  (garth)        │ │
│  └────────────────┘  └──────────────────┘  └─────────────────┘ │
│  ┌────────────────┐  ┌──────────────────┐  ┌─────────────────┐ │
│  │ Viz Service    │  │ Telemetry        │  │  Cost Tracking  │ │
│  │ (matplotlib)   │  │ (workspace pkg)  │  │                 │ │
│  └────────────────┘  └──────────────────┘  └─────────────────┘ │
└───────────────────────────┬─────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
┌───────▼────────┐  ┌───────▼────────┐  ┌──────▼──────────┐
│   Firestore    │  │ Secret Manager │  │  Cloud Logging  │
│ (user data,    │  │ (API keys,     │  │  (telemetry)    │
│  Garmin tokens,│  │  JWT secrets)  │  │                 │
│  cached data)  │  │                │  │                 │
└────────────────┘  └────────────────┘  └─────────────────┘
        │
        │ Garmin API calls (via garth)
        ▼
┌────────────────────────────┐
│   Garmin Connect API       │
│   (activities, metrics,    │
│    health data)            │
└────────────────────────────┘
```

### 2.2 Component Reuse Strategy

#### From CliniCraft (Infrastructure & Foundation)

| Component | Reuse Strategy | Customization Needed |
|-----------|----------------|---------------------|
| **Package Manager** | Direct copy (uv + pyproject.toml workspace) | Update project name, dependencies |
| **FastAPI App Structure** | Copy structure (`app/`, `services/`, `routers/`) | Add Garmin-specific routes |
| **Pydantic-AI Integration** | Copy pattern from blog_generator_service.py | New agent prompts for fitness insights |
| **Authentication** | Copy auth service (JWT + bcrypt) | Add Garmin OAuth flow + token storage |
| **Telemetry Package** | Direct copy (workspace package) | Rebrand to `selflytics-telemetry` |
| **Frontend Stack** | Copy templates, HTMX patterns | New UI for chat + visualizations |
| **CI/CD Pipeline** | Copy GitHub Actions workflows | Update project-specific secrets |
| **Terraform Modules** | Copy infra/ directory structure | Update GCP project ID, region |
| **Preview Environments** | Copy preview system + scripts | Update naming conventions |
| **Testing Framework** | Copy pytest config + test structure | New test cases for Garmin integration |
| **Pre-commit Hooks** | Direct copy (.pre-commit-config.yaml) | No changes needed |
| **Ruff Configuration** | Direct copy (pyproject.toml linting rules) | No changes needed |

#### From Garmin Agents (Garmin Integration)

| Component | Reuse Strategy | Migration Needed |
|-----------|----------------|------------------|
| **Garmin Client** | Copy GarminClient class | Remove Gradio dependencies |
| **garth Integration** | Copy token management patterns | Adapt for FastAPI async |
| **Tool Definitions** | Migrate smolagents tools → Pydantic-AI tools | Complete rewrite for new framework |
| **Data Models** | Copy Pydantic models for Garmin data | Extend for new use cases |
| **Exception Handling** | Copy MFA/auth exception patterns | Integrate with FastAPI error handlers |
| **Middleware Patterns** | Copy caching/rate limiting | Adapt for FastAPI middleware |

### 2.3 Technology Stack

| Layer | Technology | Version | Rationale |
|-------|-----------|---------|-----------|
| **Language** | Python | 3.12+ | Modern features, type hints, async support |
| **Package Manager** | uv | Latest | 10-100x faster than Poetry |
| **Web Framework** | FastAPI | ≥0.109.0 | Async, OpenAPI docs, Pydantic integration |
| **AI Framework** | Pydantic-AI | ≥1.12.0 | Structured outputs, tool calling, multi-model |
| **LLM Provider** | OpenAI API | gpt-4.1-mini (configurable) | Cost-effective, fast, structured outputs |
| **Garmin Integration** | garth | ≥0.4.0 | MFA support, token management |
| **Frontend - Templating** | Jinja2 | ≥3.1.3 | Server-side rendering, SEO-friendly |
| **Frontend - Interactivity** | HTMX | 2.x (CDN) | Partial page updates, progressive enhancement |
| **Frontend - State** | Alpine.js | 3.x (CDN) | Lightweight client state management |
| **Frontend - Styling** | TailwindCSS | 3.x (CDN) | Utility-first, no build step |
| **Visualization** | matplotlib + Pillow | Latest | AI-generated charts, PNG export |
| **Database** | Firestore (Native) | GCP | Serverless, auto-scaling, document store |
| **Secrets** | Secret Manager | GCP | Managed API keys, JWT secrets |
| **Logging** | Cloud Logging + OpenTelemetry | GCP | Centralized telemetry, trace correlation |
| **Compute** | Cloud Run | GCP | Stateless, scales to zero, pay-per-use |
| **IaC** | Terraform | ≥1.5 | Reproducible infrastructure |
| **CI/CD** | GitHub Actions | N/A | Free for public repos, Workload Identity |
| **Testing** | pytest + pytest-cov + pytest-asyncio | Latest | Async support, coverage tracking |
| **Linting** | ruff | Latest | Fast, opinionated, auto-fix |
| **Security** | bandit | Latest | Python security scanning |

---

## 3. Data Model & Storage Strategy

### 3.1 Firestore Collections

#### 3.1.1 Users Collection (`users`)

```python
{
  "user_id": "uuid-v4",
  "email": "user@example.com",
  "hashed_password": "bcrypt-hash",
  "created_at": "2025-11-11T10:00:00Z",
  "updated_at": "2025-11-11T10:00:00Z",
  "profile": {
    "display_name": "John Doe",
    "timezone": "Australia/Sydney",
    "units": "metric"  # or "imperial"
  },
  "garmin_linked": true,
  "garmin_link_date": "2025-11-11T10:05:00Z"
}
```

#### 3.1.2 Garmin Tokens Collection (`garmin_tokens`)

```python
{
  "user_id": "uuid-v4",  # Reference to users collection
  "oauth1_token": "encrypted-token",
  "oauth2_token": "encrypted-token",
  "token_expiry": "2025-12-11T10:00:00Z",
  "last_sync": "2025-11-11T15:30:00Z",
  "mfa_enabled": true,
  "created_at": "2025-11-11T10:05:00Z",
  "updated_at": "2025-11-11T15:30:00Z"
}
```

#### 3.1.3 Cached Garmin Data Collection (`garmin_data`)

```python
{
  "user_id": "uuid-v4",
  "data_type": "activities",  # or "daily_metrics", "health_snapshot", "user_profile"
  "date": "2025-11-11",
  "data": {
    # Raw Garmin API response (validated against Pydantic models)
  },
  "cached_at": "2025-11-11T15:30:00Z",
  "expires_at": "2025-11-12T15:30:00Z",
  "cache_key": "user-uuid:activities:2025-11-11"
}
```

**Cache Strategy:**
- Activities: 24-hour TTL
- Daily metrics: 6-hour TTL
- User profile: 7-day TTL
- Health snapshots: 1-hour TTL

#### 3.1.4 Chat Conversations Collection (`conversations`)

```python
{
  "conversation_id": "uuid-v4",
  "user_id": "uuid-v4",
  "title": "Running performance discussion",  # AI-generated from first message
  "created_at": "2025-11-11T16:00:00Z",
  "updated_at": "2025-11-11T16:15:00Z",
  "message_count": 8,
  "metadata": {
    "topics": ["running", "heart rate", "trend analysis"],  # AI-extracted
    "date_range_queried": ["2025-10-01", "2025-11-11"]
  }
}
```

#### 3.1.5 Chat Messages Subcollection (`conversations/{id}/messages`)

```python
{
  "message_id": "uuid-v4",
  "role": "user",  # or "assistant"
  "content": "How is my running performance trending?",
  "timestamp": "2025-11-11T16:00:00Z",
  "metadata": {
    "model_used": "gpt-4.1-mini-2025-04-14",  # For assistant messages
    "tokens": {"input": 150, "output": 420, "cached": 0, "reasoning": 0},
    "cost_usd": 0.000085,
    "latency_ms": 1250,
    "visualization_generated": true,
    "visualization_id": "uuid-v4"  # Reference to generated_visualizations
  }
}
```

#### 3.1.6 Generated Visualizations Collection (`generated_visualizations`)

```python
{
  "visualization_id": "uuid-v4",
  "user_id": "uuid-v4",
  "conversation_id": "uuid-v4",
  "message_id": "uuid-v4",
  "type": "line_chart",  # or "bar_chart", "scatter_plot", "heatmap"
  "title": "Heart Rate Trend - Last 30 Days",
  "data_query": {
    "metric": "average_heart_rate",
    "date_range": ["2025-10-12", "2025-11-11"],
    "aggregation": "daily"
  },
  "image_url": "gs://selflytics-viz/user-uuid/viz-uuid.png",  # GCS path
  "created_at": "2025-11-11T16:00:30Z",
  "expires_at": "2025-11-18T16:00:30Z"  # 7-day TTL
}
```

#### 3.1.7 User Goals Collection (`user_goals`)

```python
{
  "goal_id": "uuid-v4",
  "user_id": "uuid-v4",
  "type": "distance",  # or "duration", "frequency", "metric_threshold"
  "metric": "running_distance_km",
  "target_value": 50.0,
  "current_value": 32.5,
  "period": "monthly",
  "start_date": "2025-11-01",
  "end_date": "2025-11-30",
  "status": "in_progress",  # or "completed", "failed"
  "created_at": "2025-11-01T08:00:00Z",
  "updated_at": "2025-11-11T16:00:00Z",
  "source": "user_set"  # or "ai_inferred", "ai_suggested"
}
```

### 3.2 Data Access Patterns

| Operation | Collection | Index Needed | Query Pattern |
|-----------|-----------|--------------|---------------|
| User login | `users` | email (unique) | WHERE email == ? |
| Fetch Garmin tokens | `garmin_tokens` | user_id (unique) | WHERE user_id == ? |
| Get cached activities | `garmin_data` | user_id + data_type + date | WHERE user_id == ? AND data_type == ? AND date >= ? |
| List conversations | `conversations` | user_id + updated_at | WHERE user_id == ? ORDER BY updated_at DESC |
| Get conversation messages | `conversations/{id}/messages` | timestamp | ORDER BY timestamp ASC |
| Find visualizations | `generated_visualizations` | user_id + conversation_id | WHERE user_id == ? AND conversation_id == ? |
| Get active goals | `user_goals` | user_id + status | WHERE user_id == ? AND status == 'in_progress' |

### 3.3 Data Privacy & Security

- **Encryption at rest**: Firestore native encryption (AES-256)
- **Encryption in transit**: TLS 1.3 for all API calls
- **Token encryption**: Garmin OAuth tokens encrypted with GCP KMS before Firestore storage
- **PII redaction**: Telemetry logs redact email, tokens, sensitive health data
- **Access control**: Service account with least-privilege IAM roles
- **Data retention**:
  - Cached Garmin data: 30-day rolling window
  - Conversations: Indefinite (user can delete)
  - Visualizations: 7-day TTL (user can regenerate)

---

## 4. AI Agent Design (Pydantic-AI)

### 4.1 Agent Architecture

**Framework:** Pydantic-AI with structured outputs, tool calling, and conversational memory

**Agent Types:**

| Agent | Purpose | Output Type | Tools Available |
|-------|---------|-------------|-----------------|
| **Chat Agent** | Natural language conversation | `ChatResponse` | garmin_tools, viz_tools, goal_tools |
| **Visualization Agent** | Generate charts from queries | `VisualizationSpec` | data_query_tool, chart_generator |
| **Goal Inference Agent** | Extract goals from conversation | `GoalSuggestion` | None (pure inference) |

### 4.2 Chat Agent Design

```python
from pydantic import BaseModel, Field
from pydantic_ai import Agent, Tool

class ChatResponse(BaseModel):
    """Structured response from chat agent."""
    message: str = Field(..., description="Natural language response to user")
    visualization_requested: bool = Field(default=False, description="Whether to generate a chart")
    visualization_spec: Optional[VisualizationSpec] = None
    suggested_followup: Optional[str] = Field(None, description="Suggested next question")
    data_sources_used: list[str] = Field(default_factory=list, description="Garmin data types queried")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence in response accuracy")

chat_agent = Agent(
    model="openai:gpt-4.1-mini-2025-04-14",  # Configurable via env var
    system_prompt="""You are a fitness data analyst assistant for Selflytics.

    Your role:
    - Answer user questions about their Garmin fitness data
    - Provide insights on trends, patterns, and progress
    - Suggest visualizations when appropriate
    - Be encouraging but accurate (don't exaggerate progress)
    - Respect privacy (never share data outside conversation)

    Available data:
    - Running, cycling, swimming activities
    - Heart rate, steps, sleep metrics
    - User-defined goals and progress

    Guidelines:
    - Use metric units unless user specifies imperial
    - Reference specific dates/activities when possible
    - Suggest visualizations for trend questions
    - Acknowledge data limitations (e.g., "Based on last 30 days...")
    """,
    output_type=ChatResponse,
    tools=[
        garmin_activity_tool,
        garmin_metrics_tool,
        goal_status_tool,
        visualization_request_tool
    ]
)
```

### 4.3 Pydantic-AI Tools (Migrated from smolagents)

#### From Garmin Agents smolagents → Pydantic-AI Migration

**Before (smolagents):**
```python
from smolagents import tool

@tool
def get_activities(start_date: str, end_date: str, activity_type: Optional[str] = None) -> dict:
    """Get user activities from Garmin Connect."""
    # Implementation using GarminClient
    pass
```

**After (Pydantic-AI):**
```python
from pydantic import BaseModel, Field
from pydantic_ai import Tool

class ActivityQuery(BaseModel):
    start_date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    end_date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    activity_type: Optional[str] = Field(None, description="running, cycling, swimming, etc.")

async def get_activities(query: ActivityQuery, user_id: str) -> dict:
    """Get user activities from Garmin Connect.

    Queries Garmin API for activities in date range, with optional type filtering.
    Returns cached data if available (24h TTL), otherwise fetches fresh data.
    """
    garmin_client = await get_user_garmin_client(user_id)
    # Check cache first
    cached = await check_activity_cache(user_id, query.start_date, query.end_date)
    if cached:
        return cached

    # Fetch from Garmin API
    activities = await garmin_client.get_activities(
        start_date=query.start_date,
        end_date=query.end_date,
        activity_type=query.activity_type
    )

    # Cache for 24 hours
    await cache_activities(user_id, activities, ttl=86400)
    return activities

garmin_activity_tool = Tool(
    name="get_activities",
    description="Retrieve user activities from Garmin Connect in a date range",
    function=get_activities
)
```

**Key Migration Changes:**
1. Input validation moved to Pydantic models (not function signature)
2. Async/await required (FastAPI is async)
3. User context passed explicitly (no thread-local storage)
4. Caching integrated directly in tool (not middleware)
5. Error handling returns structured exceptions (not raw dicts)

#### Tool Inventory (Migrated from Garmin Agents)

| Garmin Agents Tool | Status | Pydantic-AI Equivalent | Changes Needed |
|-------------------|--------|----------------------|----------------|
| `get_activities` | ✅ Migrate | `garmin_activity_tool` | Add async, cache integration, Pydantic input |
| `get_user_profile` | ✅ Migrate | `garmin_profile_tool` | Add async, cache (7-day TTL) |
| `get_daily_metrics` | ✅ Migrate | `garmin_metrics_tool` | Add async, cache (6-hour TTL) |
| `get_health_snapshot` | ✅ Migrate | `garmin_health_tool` | Add async, cache (1-hour TTL) |
| `search_activities` | ⚠️ Refactor | `activity_search_tool` | Combine with `get_activities`, use filtering |
| `summarize_week` | ❌ Remove | N/A | Replaced by agent reasoning |
| `plot_trend` | ✅ Migrate | `visualization_request_tool` | Major refactor (see §4.4) |

### 4.4 Visualization Generation

**Two-Stage Process:**

**Stage 1: Visualization Specification (Chat Agent)**
```python
class VisualizationSpec(BaseModel):
    """Specification for generating a chart."""
    chart_type: Literal["line", "bar", "scatter", "heatmap"]
    title: str = Field(..., max_length=100)
    x_axis: str = Field(..., description="X-axis metric/dimension")
    y_axis: str = Field(..., description="Y-axis metric")
    data_query: dict = Field(..., description="Parameters to fetch data")
    date_range: tuple[str, str] = Field(..., description="Start and end dates")
    aggregation: Optional[str] = Field(None, description="daily, weekly, monthly")
```

**Stage 2: Chart Generation (Visualization Service)**
```python
from matplotlib import pyplot as plt
from io import BytesIO
from PIL import Image

async def generate_chart(spec: VisualizationSpec, user_id: str) -> str:
    """Generate chart image from spec, return GCS URL."""

    # Fetch data based on spec.data_query
    data = await fetch_data_for_visualization(spec, user_id)

    # Generate matplotlib chart
    fig, ax = plt.subplots(figsize=(10, 6))

    if spec.chart_type == "line":
        ax.plot(data["x"], data["y"])
    elif spec.chart_type == "bar":
        ax.bar(data["x"], data["y"])
    # ... other chart types

    ax.set_title(spec.title)
    ax.set_xlabel(spec.x_axis)
    ax.set_ylabel(spec.y_axis)

    # Save to BytesIO
    buf = BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    buf.seek(0)

    # Upload to GCS
    viz_id = str(uuid.uuid4())
    gcs_path = f"gs://selflytics-viz/{user_id}/{viz_id}.png"
    await upload_to_gcs(buf, gcs_path)

    # Save metadata to Firestore
    await save_visualization_metadata(viz_id, user_id, spec, gcs_path)

    return gcs_path
```

**Integration in Chat Response:**

```python
# User asks: "Show me my running pace over the last month"

# Chat agent generates:
ChatResponse(
    message="Here's your running pace trend for the last 30 days. You've improved from 6:30/km to 6:05/km!",
    visualization_requested=True,
    visualization_spec=VisualizationSpec(
        chart_type="line",
        title="Running Pace - Last 30 Days",
        x_axis="Date",
        y_axis="Average Pace (min/km)",
        data_query={"metric": "average_pace", "activity_type": "running"},
        date_range=("2025-10-12", "2025-11-11"),
        aggregation="daily"
    ),
    suggested_followup="Would you like to see your heart rate during these runs?",
    data_sources_used=["activities"],
    confidence=0.95
)

# Visualization service generates chart and returns URL
# HTMX loads image into chat interface
```

### 4.5 Conversational Memory

**Approach:** Store full conversation history in Firestore, pass last N messages as context

```python
async def get_conversation_context(conversation_id: str, limit: int = 10) -> list[dict]:
    """Fetch last N messages for context."""
    messages = await firestore.collection("conversations").document(conversation_id).collection("messages").order_by("timestamp", direction="DESC").limit(limit).get()

    return [
        {"role": msg["role"], "content": msg["content"]}
        for msg in reversed(messages)  # Chronological order
    ]

# Pass to agent
context = await get_conversation_context(conversation_id)
response = await chat_agent.run(
    user_message,
    message_history=context  # Pydantic-AI context parameter
)
```

**Context Window Management:**
- Default: Last 10 messages (~ 2-5k tokens)
- Smart truncation: If exceeds 8k tokens, summarize older messages
- Conversation reset: User can start fresh conversation

### 4.6 Cost Tracking & Token Management

**Pattern from CliniCraft** (reuse `cost_tracking.py`):

```python
class ChatUsage(BaseModel):
    """Token usage for a single chat exchange."""
    input_tokens: int
    output_tokens: int
    cached_tokens: int = 0
    reasoning_tokens: int = 0
    cost_usd: float
    model: str
    timestamp: datetime

async def track_chat_usage(response: ChatResponse, message_id: str):
    """Save usage metrics to Firestore."""
    usage = ChatUsage(
        input_tokens=response.usage.input_tokens,
        output_tokens=response.usage.output_tokens,
        cost_usd=calculate_cost(response.usage, model="gpt-4.1-mini"),
        model="gpt-4.1-mini-2025-04-14",
        timestamp=datetime.utcnow()
    )

    # Attach to message metadata
    await firestore.collection("conversations").document(conversation_id).collection("messages").document(message_id).update({
        "metadata.tokens": usage.dict(),
        "metadata.cost_usd": usage.cost_usd
    })
```

---

## 5. Frontend Architecture

### 5.1 Progressive Enhancement Stack

**Philosophy:** Server-first rendering with layered enhancements

**Layer 1 (Base):** Jinja2 templates, forms submit with full page reload
**Layer 2 (+HTMX):** Partial HTML updates, no page reload
**Layer 3 (+Alpine.js):** Client state, animations, modals

### 5.2 Page Structure

#### 5.2.1 Dashboard (`/dashboard`)

**Purpose:** Overview of recent activity, goals, conversation history

**Jinja2 Template Structure:**
```html
{% extends "base.html" %}

{% block content %}
<div class="container mx-auto p-6">
  <!-- Recent Activities Card -->
  <div class="bg-white rounded-lg shadow p-6 mb-6">
    <h2 class="text-2xl font-bold mb-4">Recent Activities</h2>
    {% include "partials/activity_list.html" %}
  </div>

  <!-- Active Goals Card -->
  <div class="bg-white rounded-lg shadow p-6 mb-6">
    <h2 class="text-2xl font-bold mb-4">Active Goals</h2>
    {% include "partials/goal_progress.html" %}
  </div>

  <!-- Conversation History -->
  <div class="bg-white rounded-lg shadow p-6">
    <h2 class="text-2xl font-bold mb-4">Recent Conversations</h2>
    {% include "partials/conversation_list.html" %}
  </div>
</div>
{% endblock %}
```

#### 5.2.2 Chat Interface (`/chat` or `/chat/{conversation_id}`)

**Purpose:** Main conversation interface with AI-generated visualizations

**HTMX Integration:**
```html
<div class="chat-container" x-data="{ sending: false }">
  <!-- Message History (scrollable) -->
  <div id="messages" class="messages-area overflow-y-auto h-96 p-4">
    {% for msg in messages %}
      {% if msg.role == 'user' %}
        <div class="message user-message">{{ msg.content }}</div>
      {% else %}
        <div class="message assistant-message">
          {{ msg.content }}
          {% if msg.visualization_id %}
            <img src="/viz/{{ msg.visualization_id }}" alt="{{ msg.viz_title }}" class="mt-4 rounded">
          {% endif %}
        </div>
      {% endif %}
    {% endfor %}
  </div>

  <!-- Input Form (HTMX-enhanced) -->
  <form
    hx-post="/api/chat/send"
    hx-target="#messages"
    hx-swap="beforeend"
    hx-on::before-request="sending = true"
    hx-on::after-request="sending = false; $refs.input.value = ''"
    class="flex gap-2 p-4 border-t"
  >
    <input
      x-ref="input"
      type="text"
      name="message"
      placeholder="Ask about your fitness data..."
      class="flex-1 border rounded px-4 py-2"
      :disabled="sending"
    >
    <button
      type="submit"
      class="bg-blue-600 text-white px-6 py-2 rounded"
      :disabled="sending"
      x-text="sending ? 'Thinking...' : 'Send'"
    ></button>
  </form>
</div>
```

**API Endpoint Returns Partial HTML:**
```python
@router.post("/api/chat/send")
async def send_message(message: str, conversation_id: str, current_user: User):
    """HTMX endpoint - returns partial HTML for new messages."""

    # Save user message
    user_msg = await save_message(conversation_id, "user", message)

    # Get AI response
    response = await chat_agent.run(message, user_id=current_user.id)

    # Generate visualization if requested
    viz_url = None
    if response.visualization_requested:
        viz_url = await generate_chart(response.visualization_spec, current_user.id)

    # Save assistant message
    assistant_msg = await save_message(
        conversation_id,
        "assistant",
        response.message,
        visualization_url=viz_url
    )

    # Return partial HTML (both user + assistant messages)
    return templates.TemplateResponse(
        "partials/messages.html",
        {
            "messages": [user_msg, assistant_msg],
            "request": request
        }
    )
```

#### 5.2.3 Garmin Linking Flow (`/settings/garmin`)

**Purpose:** OAuth flow to link Garmin account

**Flow:**
1. User clicks "Link Garmin Account"
2. Redirect to Garmin OAuth consent page
3. Garmin redirects back to `/auth/garmin/callback?code=...`
4. Exchange code for tokens, save to Firestore (encrypted)
5. Redirect to dashboard with success message

**Template:**
```html
{% if current_user.garmin_linked %}
  <div class="bg-green-50 border border-green-200 rounded p-4">
    <p class="text-green-800">✓ Garmin account linked</p>
    <p class="text-sm text-gray-600">Last sync: {{ current_user.garmin_last_sync | format_datetime }}</p>
    <button
      hx-post="/api/garmin/sync"
      hx-swap="outerHTML"
      class="mt-2 text-blue-600 underline"
    >
      Sync now
    </button>
  </div>
{% else %}
  <div class="bg-yellow-50 border border-yellow-200 rounded p-4">
    <p class="text-yellow-800">Garmin account not linked</p>
    <a href="/auth/garmin/link" class="mt-2 inline-block bg-blue-600 text-white px-4 py-2 rounded">
      Link Garmin Account
    </a>
  </div>
{% endif %}
```

### 5.3 Responsive Design

**Approach:** Mobile-first with TailwindCSS responsive utilities

**Breakpoints:**
- `sm`: 640px (tablet)
- `md`: 768px (desktop)
- `lg`: 1024px (large desktop)

**Example (Chat Interface):**
```html
<div class="
  grid
  grid-cols-1
  md:grid-cols-[300px_1fr]  <!-- Sidebar on desktop -->
  gap-4
  h-screen
">
  <!-- Sidebar (conversation list) - hidden on mobile -->
  <aside class="hidden md:block bg-gray-50 p-4">
    <!-- Conversation list -->
  </aside>

  <!-- Main chat area -->
  <main class="flex flex-col">
    <!-- Chat messages + input -->
  </main>
</div>
```

---

## 6. Infrastructure & Deployment

### 6.1 GCP Resources (Terraform Managed)

**Project:** `selflytics-prod` (to be created)
**Region:** `australia-southeast1` (Sydney)
**Production Domain:** `selflytics.anbaricideas.com`

| Resource | Type | Configuration | Cost Estimate |
|----------|------|---------------|---------------|
| **Cloud Run Service** | Compute | Min 0, Max 100 instances, 2 CPU, 512MB RAM | ~$10/month (100 users) |
| **Firestore** | Database | Native mode, australia-southeast1 | ~$5/month (100 users) |
| **Secret Manager** | Secrets | 3 secrets (JWT, OpenAI, Garmin OAuth) | ~$0.60/month |
| **Cloud Logging** | Telemetry & Observability | OpenTelemetry integration, 30-day retention | ~$2/month |
| **Cloud Storage (GCS)** | Visualization storage | Standard class, 30-day lifecycle | ~$1/month |
| **Artifact Registry** | Docker images | Docker repository, 90-day cleanup | ~$1/month |
| **Cloud Build** | CI/CD (optional) | GitHub trigger (or GitHub Actions) | ~$0 (free tier) |

**Total estimated cost:** ~$20-25/month for 100 active users

### 6.2 Terraform Module Structure (Copy from CliniCraft)

```
infra/
├── modules/
│   ├── cloud_run/          # Cloud Run service + IAM
│   ├── cloud_run_preview/  # Preview environment module
│   ├── firestore/          # Firestore database + indexes
│   ├── secrets/            # Secret Manager + IAM
│   ├── storage/            # GCS buckets (viz storage)
│   └── dns/                # (Future) Custom domain setup
├── environments/
│   ├── dev/
│   │   ├── main.tf         # Dev environment config
│   │   ├── backend.tf      # GCS backend config
│   │   └── terraform.tfvars
│   └── prod/               # (Future) Production environment
└── scripts/
    ├── deploy.sh           # Main deployment script
    ├── preview             # Preview environment CLI
    └── lib/                # Shared shell libraries
```

### 6.3 CI/CD Pipeline (GitHub Actions)

**Workflow Files:**

| Workflow | Trigger | Purpose | Jobs |
|----------|---------|---------|------|
| **ci.yml** | PR to main, push to main | Quality gates | lint, test, security, type-check, terraform-validate |
| **cd.yml** | CI success on main | Deploy to dev | build-push, terraform-apply, deploy-cloud-run, validate |
| **preview.yml** | Push to `feat/**` | Deploy preview | build-push-preview, terraform-apply-preview |
| **preview-cleanup.yml** | PR closed, branch deleted | Cleanup preview | terraform-destroy-preview |

**Authentication:** Workload Identity Federation (no long-lived keys)

```yaml
# .github/workflows/cd.yml (excerpt)
- name: Authenticate to Google Cloud
  uses: google-github-actions/auth@v1
  with:
    workload_identity_provider: ${{ secrets.WIF_PROVIDER }}
    service_account: ${{ secrets.WIF_SERVICE_ACCOUNT }}

- name: Build and Push Docker Image
  run: |
    docker build -t australia-southeast1-docker.pkg.dev/selflytics-prod/selflytics/backend:${{ github.sha }} backend/
    docker push australia-southeast1-docker.pkg.dev/selflytics-prod/selflytics/backend:${{ github.sha }}

- name: Deploy to Cloud Run
  run: |
    cd infra/environments/dev
    terraform apply -auto-approve -var="image_tag=${{ github.sha }}"
```

### 6.4 Preview Environment System

**Goal:** Auto-deploy feature branches to isolated Cloud Run instances

**Naming Convention:**
- Service: `selflytics-preview-{branch-name-sanitized}`
- URL: `https://selflytics-preview-{branch-name}-{random-id}.run.app`

**Lifecycle:**
1. Push to `feat/chat-visualizations` → trigger `preview.yml`
2. Build Docker image with tag `preview-chat-visualizations`
3. Terraform creates isolated Cloud Run service + Firestore namespace
4. GitHub bot comments on PR with preview URL
5. PR closed → `preview-cleanup.yml` destroys resources

**CLI Tool (copy from CliniCraft):**
```bash
./infra/scripts/preview status          # Overview of all previews
./infra/scripts/preview list            # Detailed listing
./infra/scripts/preview dashboard       # Interactive management UI
./infra/scripts/preview cleanup         # Remove orphaned previews
./infra/scripts/preview count           # CI-friendly count validation
```

### 6.5 Secrets Management

**Secrets in Secret Manager:**

| Secret Name | Purpose | Rotation |
|-------------|---------|----------|
| `jwt-secret-key` | JWT token signing | 90 days |
| `openai-api-key` | OpenAI API authentication | Manual (when compromised) |
| `garmin-oauth-client-secret` | Garmin OAuth flow | Manual (Garmin-managed) |

**Access Pattern:**
```python
from google.cloud import secretmanager

async def get_secret(secret_name: str) -> str:
    """Fetch secret from Secret Manager with caching."""
    client = secretmanager.SecretManagerServiceAsyncClient()
    name = f"projects/selflytics-prod/secrets/{secret_name}/versions/latest"
    response = await client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")

# Usage
OPENAI_API_KEY = await get_secret("openai-api-key")
```

---

## 7. Testing & Quality Standards

### 7.1 Testing Strategy (TDD Workflow)

**Philosophy:** Test-first development with 80%+ coverage requirement

**Test Pyramid:**
```
        ┌───────────┐
        │    E2E    │  10% - Full user workflows (Playwright)
        │   Tests   │
        └───────────┘
      ┌───────────────┐
      │  Integration  │  30% - API endpoints, database interactions
      │     Tests     │
      └───────────────┘
    ┌───────────────────┐
    │   Unit Tests      │  60% - Services, models, utilities
    │                   │
    └───────────────────┘
```

### 7.2 Test Organization

```
backend/tests/
├── unit/
│   ├── services/
│   │   ├── test_chat_service.py       # Chat agent logic
│   │   ├── test_garmin_service.py     # Garmin API interactions
│   │   ├── test_visualization_service.py
│   │   └── test_auth_service.py
│   ├── models/
│   │   └── test_pydantic_models.py
│   └── utils/
│       └── test_cache.py
├── integration/
│   ├── routers/
│   │   ├── test_chat_router.py        # POST /api/chat/send
│   │   ├── test_garmin_router.py      # Garmin OAuth flow
│   │   └── test_auth_router.py        # Login, register, JWT
│   └── test_firestore_integration.py
├── e2e/
│   ├── test_user_journey.py           # Register → Link Garmin → Chat → Viz
│   └── test_conversation_flow.py
└── conftest.py                        # Shared fixtures
```

### 7.3 Key Test Fixtures (from CliniCraft)

```python
# backend/tests/conftest.py

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db.firestore import get_firestore_client
from unittest.mock import AsyncMock

@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)

@pytest.fixture
def mock_firestore(monkeypatch):
    """Mock Firestore client for unit tests."""
    mock_client = AsyncMock()
    monkeypatch.setattr("app.db.firestore.firestore_client", mock_client)
    return mock_client

@pytest.fixture
def mock_garmin_client(monkeypatch):
    """Mock GarminClient for testing without real API calls."""
    mock_client = AsyncMock()
    mock_client.get_activities.return_value = [
        {"activityId": 123, "activityName": "Morning Run", "distance": 5000}
    ]
    monkeypatch.setattr("app.services.garmin_service.GarminClient", lambda: mock_client)
    return mock_client

@pytest.fixture
def mock_openai(monkeypatch):
    """Mock OpenAI API for predictable AI responses."""
    mock_response = {
        "message": "Your running pace has improved by 15 seconds/km!",
        "visualization_requested": True,
        "confidence": 0.92
    }
    monkeypatch.setattr("pydantic_ai.Agent.run", AsyncMock(return_value=mock_response))
    return mock_response

@pytest.fixture
async def test_user(mock_firestore):
    """Create a test user in mocked Firestore."""
    user_data = {
        "user_id": "test-user-123",
        "email": "test@example.com",
        "hashed_password": "bcrypt-hash",
        "garmin_linked": True
    }
    await mock_firestore.collection("users").document("test-user-123").set(user_data)
    return user_data
```

### 7.4 Example Tests

#### 7.4.1 Unit Test (Chat Service)

```python
# tests/unit/services/test_chat_service.py

import pytest
from app.services.chat_service import ChatService
from app.models.chat import ChatResponse

@pytest.mark.asyncio
async def test_chat_service_generates_visualization_for_trend_query(
    mock_garmin_client,
    mock_openai
):
    """Test that trend queries trigger visualization generation."""

    service = ChatService(user_id="test-user-123")

    # User asks about trend
    response = await service.send_message(
        message="Show me my running pace over the last month",
        conversation_id="conv-456"
    )

    # Assert response structure
    assert isinstance(response, ChatResponse)
    assert response.visualization_requested is True
    assert response.visualization_spec.chart_type == "line"
    assert "pace" in response.message.lower()

    # Assert Garmin API was called
    mock_garmin_client.get_activities.assert_called_once()
```

#### 7.4.2 Integration Test (API Endpoint)

```python
# tests/integration/routers/test_chat_router.py

import pytest
from fastapi.testclient import TestClient

def test_chat_send_endpoint_returns_partial_html(client, test_user, mock_openai):
    """Test POST /api/chat/send returns HTMX-compatible HTML fragment."""

    # Authenticate
    login_response = client.post("/api/auth/login", json={
        "email": "test@example.com",
        "password": "password123"
    })
    token = login_response.json()["access_token"]

    # Send chat message
    response = client.post(
        "/api/chat/send",
        data={"message": "How am I doing?", "conversation_id": "conv-123"},
        headers={"Authorization": f"Bearer {token}"}
    )

    # Assert response
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "assistant-message" in response.text  # HTML class name
    assert mock_openai["message"] in response.text
```

#### 7.4.3 E2E Test (Full User Journey)

```python
# tests/e2e/test_user_journey.py

import pytest
from playwright.async_api import async_playwright

@pytest.mark.e2e
@pytest.mark.asyncio
async def test_complete_user_journey():
    """Test full flow: Register → Link Garmin → Chat → View Visualization."""

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        # 1. Register
        await page.goto("http://localhost:8000/register")
        await page.fill("input[name=email]", "newuser@example.com")
        await page.fill("input[name=password]", "SecurePass123!")
        await page.click("button[type=submit]")
        await page.wait_for_url("http://localhost:8000/dashboard")

        # 2. Link Garmin (mock OAuth flow)
        await page.click("text=Link Garmin Account")
        # ... mock Garmin OAuth ...
        await page.wait_for_selector("text=✓ Garmin account linked")

        # 3. Start conversation
        await page.click("text=New Conversation")
        await page.fill("input[name=message]", "Show my running pace trend")
        await page.click("button:has-text('Send')")

        # 4. Wait for AI response with visualization
        await page.wait_for_selector(".assistant-message")
        await page.wait_for_selector("img[alt*='Running Pace']")

        # 5. Assert visualization loaded
        viz_element = await page.query_selector("img[alt*='Running Pace']")
        assert viz_element is not None

        await browser.close()
```

### 7.5 Coverage Requirements

**Enforcement:**
```toml
# pyproject.toml
[tool.pytest.ini_options]
addopts = "--cov=app --cov-report=term-missing --cov-report=html --cov-fail-under=80"
```

**Pre-commit Hook:**
```yaml
# .pre-commit-config.yaml
- repo: local
  hooks:
    - id: pytest-coverage
      name: pytest with coverage
      entry: pytest --cov=app --cov-fail-under=80
      language: system
      pass_filenames: false
      always_run: true
```

**CI Gate:**
```yaml
# .github/workflows/ci.yml
- name: Run tests with coverage
  run: |
    cd backend
    uv run pytest --cov=app --cov-report=xml --cov-fail-under=80

- name: Upload coverage to Codecov
  uses: codecov/codecov-action@v3
  with:
    file: ./backend/coverage.xml
    fail_ci_if_error: true
```

---

## 8. Security & Privacy

### 8.1 Authentication & Authorization

**Authentication:** JWT tokens (RS256 signing)

**Flow:**
1. User registers/logs in → receives JWT access token (30-min expiry) + refresh token (7-day expiry)
2. Client stores tokens in `httpOnly` cookies (secure, sameSite=strict)
3. Subsequent requests include JWT in `Authorization: Bearer <token>` header
4. FastAPI middleware validates JWT, extracts user_id, injects into request context

**Password Security:**
- bcrypt hashing with cost factor 12
- Minimum password requirements: 12 characters, 1 uppercase, 1 number, 1 special character
- Rate limiting: 5 failed login attempts → 15-minute lockout

**Garmin OAuth Security:**
- OAuth 1.0 + OAuth 2.0 tokens encrypted with GCP KMS before storage
- Tokens never logged or exposed in API responses
- MFA support via garth library

### 8.2 Data Privacy

**PII Redaction in Logs:**
```python
# app/utils/redact.py (copy from Garmin Agents)

import re

PII_PATTERNS = [
    (re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'), '[EMAIL]'),
    (re.compile(r'\b\d{3}-\d{2}-\d{4}\b'), '[SSN]'),
    (re.compile(r'oauth[_-]?token["\']?\s*[:=]\s*["\']?([a-zA-Z0-9_-]+)', re.IGNORECASE), 'oauth_token=[REDACTED]'),
]

def redact_sensitive_data(text: str) -> str:
    """Redact PII from log messages."""
    for pattern, replacement in PII_PATTERNS:
        text = pattern.sub(replacement, text)
    return text
```

**Pre-commit Hook Enforcement:**
```yaml
- id: check-no-pii-in-logs
  name: Check for PII in log statements
  entry: 'grep -rn "logger\.(info|debug|warning|error).*@" --include="*.py" backend/app/'
  language: system
  pass_filenames: false
  # Fails if email patterns found in logger calls
```

### 8.3 API Security

**Rate Limiting (FastAPI Middleware):**
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/api/chat/send")
@limiter.limit("10/minute")  # Max 10 chat messages per minute
async def send_message(...):
    pass
```

**CORS Configuration:**
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://selflytics.com"],  # Production domain only
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)
```

**Input Validation:**
- All inputs validated via Pydantic models
- Max message length: 2000 characters
- Date range limits: Max 2 years of historical data per query
- File upload size limits: N/A (no file uploads in MVP)

### 8.4 Dependency Security

**Bandit Security Scanning:**
```yaml
# .github/workflows/ci.yml
- name: Run Bandit security scan
  run: |
    cd backend
    uv run bandit -r app/ -f json -o bandit-report.json
    uv run bandit -r app/ --exit-zero  # Fail on high-severity issues
```

**Dependency Auditing:**
```bash
# Pre-commit hook
uv pip check  # Verify no conflicting dependencies
uv pip list --outdated  # Check for outdated packages
```

### 8.5 Compliance Considerations

**GDPR/CCPA Requirements (Future):**
- User data export endpoint: `GET /api/user/data-export` → JSON download
- Account deletion: `DELETE /api/user/account` → hard delete all data
- Data retention policies: 30-day rolling window for cached Garmin data

**Health Data Regulations:**
- Not a medical device (disclaimer in UI)
- No health diagnoses or medical advice
- Terms of Service clarifies fitness insights only

---

## 9. Development Approach (Spike → Phases)

### 9.1 Initial Spike (Validation Phase)

**Goal:** Validate core technical assumptions before committing to full implementation

**Duration:** 1 week (40 hours)

**Deliverables:**
1. **Pydantic-AI Chat Agent Prototype**
   - Minimal agent that can query mock Garmin data
   - Structured output (ChatResponse model)
   - Tool calling with 2-3 basic tools (get_activities, get_metrics)
   - Demonstrates feasibility of smolagents → Pydantic-AI migration

2. **Garmin Integration Proof-of-Concept**
   - Authenticate with Garmin (MFA flow)
   - Fetch 1 week of activities
   - Cache in local JSON file (not Firestore yet)
   - Validates garth library compatibility with FastAPI async

3. **Visualization Generation**
   - Generate 1 chart type (line chart) from mock data
   - Save to local filesystem (not GCS yet)
   - Embed in simple HTML response
   - Validates matplotlib → PNG → HTML workflow

4. **Decision Point:** Proceed to Phase 1 if:
   - Pydantic-AI agent produces coherent, actionable responses
   - Garmin OAuth + data fetch works reliably
   - Visualization generation is fast enough (<3 seconds)

**Tech Stack for Spike:**
- FastAPI (single `main.py` file)
- Pydantic-AI with OpenAI gpt-4.1-mini
- garth library
- matplotlib
- Local storage (no Firestore/GCP yet)

### 9.2 Phased Implementation

**Phase 1: Infrastructure Foundation** (2 weeks, 80 hours)

**Goal:** Establish production-ready infrastructure and authentication

**Deliverables:**
- [ ] GCP project setup (`selflytics-prod`)
- [ ] Terraform modules (Cloud Run, Firestore, Secret Manager, GCS, Cloud Logging)
- [ ] GitHub Actions CI/CD pipeline (ci.yml, cd.yml)
- [ ] Complete project structure (copy from CliniCraft, all folders from day one)
- [ ] Authentication service (JWT + bcrypt)
- [ ] User registration/login endpoints
- [ ] Frontend templates (base.html, login.html, register.html, dashboard.html)
- [ ] Telemetry workspace package with Cloud Logging backend
- [ ] 80%+ test coverage for auth flows

**Success Criteria:**
- User can register, login, access dashboard
- CI passes all quality gates (lint, test, security)
- Infrastructure deployed to `dev` environment
- Preview environment system functional

---

**Phase 2: Garmin Integration** (2 weeks, 80 hours)

**Goal:** Production-ready Garmin OAuth and data fetching

**Deliverables:**
- [ ] Garmin OAuth flow (link account from settings)
- [ ] GarminClient service (async wrapper around garth)
- [ ] Token storage in Firestore (encrypted with KMS)
- [ ] Data caching layer (Firestore with TTL)
- [ ] Pydantic models for Garmin data (activities, metrics, health)
- [ ] Garmin sync endpoint (manual trigger + background job)
- [ ] Error handling for MFA, token expiry, API rate limits
- [ ] 80%+ test coverage (mocked Garmin API)

**Success Criteria:**
- User can link Garmin account via OAuth
- Activities from last 30 days cached in Firestore
- Cache invalidation works (24-hour TTL)
- MFA flow completes successfully (tested manually)

---

**Phase 3: Chat Interface + AI Agent** (3 weeks, 120 hours)

**Goal:** Natural language chat with AI-powered insights

**Deliverables:**
- [ ] Pydantic-AI chat agent with tools (get_activities, get_metrics, get_profile)
- [ ] System prompts for fitness insights
- [ ] Conversation management (Firestore storage)
- [ ] Chat UI (Jinja2 + HTMX)
- [ ] Message history context (last 10 messages)
- [ ] Cost tracking for AI usage
- [ ] Conversational memory (summarization for long threads)
- [ ] Goal inference agent (extract goals from conversation)
- [ ] 80%+ test coverage (mocked OpenAI)

**Success Criteria:**
- User can ask "How am I doing?" and get relevant insights
- Agent cites specific activities/dates in responses
- Conversation history persists across sessions
- Token usage tracked and costs under $0.05 per conversation

---

**Phase 4: Visualization Generation** (2 weeks, 80 hours)

**Goal:** AI-generated charts in response to user queries

**Deliverables:**
- [ ] Visualization service (matplotlib + GCS storage)
- [ ] VisualizationSpec model (chart type, data query, styling)
- [ ] 4 chart types (line, bar, scatter, heatmap)
- [ ] HTMX integration (lazy-load images in chat)
- [ ] Visualization metadata (Firestore)
- [ ] 7-day TTL + cleanup job
- [ ] Regeneration on request
- [ ] 80%+ test coverage (mocked chart generation)

**Success Criteria:**
- User query "Show my running pace trend" generates line chart
- Chart renders in <5 seconds
- Images stored in GCS and served via signed URL
- Cleanup job removes expired visualizations

---

**Phase 5: Goals & Polish** (1 week, 40 hours)

**Goal:** Goal tracking, UI polish, performance optimization

**Deliverables:**
- [ ] User goals (set, track, AI suggestions)
- [ ] Dashboard improvements (recent activities, goal progress)
- [ ] Performance optimization (query caching, lazy loading)
- [ ] Error handling improvements (user-friendly messages)
- [ ] Documentation (user guide, API docs)
- [ ] E2E tests for complete user journeys
- [ ] 80%+ test coverage maintained

**Success Criteria:**
- User can set goal "Run 50km this month" and track progress
- Dashboard loads in <2 seconds
- All error states have helpful messages
- Documentation covers all user-facing features

---

**Phase 6: Launch Preparation** (1 week, 40 hours)

**Goal:** Production readiness, monitoring, beta launch

**Deliverables:**
- [ ] Production environment setup (Terraform + Cloud Run)
- [ ] Custom domain + SSL (selflytics.anbaricideas.com)
- [ ] Monitoring dashboards (Cloud Logging, uptime checks)
- [ ] Cost alerts (budget thresholds)
- [ ] Privacy policy + Terms of Service
- [ ] Beta user testing (~10 users)
- [ ] Bug fixes from beta feedback

**Success Criteria:**
- Production deployment successful at selflytics.anbaricideas.com
- Monitoring alerts configured
- 10 beta users complete full journey
- No critical bugs reported

---

### 9.3 Total Effort Estimate

| Phase | Duration | Effort (hours) |
|-------|----------|----------------|
| **Spike** | 1 week | 40 |
| **Phase 1** (Infrastructure) | 2 weeks | 80 |
| **Phase 2** (Garmin Integration) | 2 weeks | 80 |
| **Phase 3** (Chat + AI) | 3 weeks | 120 |
| **Phase 4** (Visualization) | 2 weeks | 80 |
| **Phase 5** (Goals + Polish) | 1 week | 40 |
| **Phase 6** (Launch Prep) | 1 week | 40 |
| **TOTAL** | **12 weeks** | **480 hours** |

**Assumptions:**
- 40 hours/week (full-time)
- 20% buffer included for debugging, refactoring
- No major scope changes during development

---

## 10. Success Criteria & Metrics

### 10.1 MVP Success Criteria

**User Experience:**
- [ ] User can register and link Garmin account in <5 minutes
- [ ] Chat responds with insights in <10 seconds (p95 latency)
- [ ] Visualizations generate in <5 seconds
- [ ] 90%+ uptime (Cloud Run availability)

**Technical Quality:**
- [ ] 80%+ test coverage maintained
- [ ] All CI quality gates pass (lint, test, security, type-check)
- [ ] Zero high-severity security vulnerabilities (Bandit scan)
- [ ] API latency p95 <2 seconds

**Cost Efficiency:**
- [ ] Infrastructure costs <$50/month for 100 active users
- [ ] AI costs <$0.10 per user per month
- [ ] Total cost per user <$1/month

### 10.2 Post-Launch Metrics

**Engagement:**
- Daily active users (DAU)
- Conversations per user per week
- Average conversation length (messages)
- Visualization generation rate (% of conversations with charts)

**Performance:**
- API latency (p50, p95, p99)
- Error rate (<1%)
- Cache hit rate (>70% for Garmin data)
- AI response quality (user feedback: thumbs up/down)

**Cost:**
- Cloud Run costs per user
- Firestore read/write costs
- OpenAI API costs per conversation
- GCS storage costs (visualizations)

---

## 11. Future Expansion (Post-MVP)

### 11.1 Additional Data Sources

- **Fitbit** (via Fitbit Web API)
- **Apple Health** (via HealthKit export + manual upload)
- **Strava** (activities + social features)
- **Manual CSV uploads** (generic quantified self data)

### 11.2 Advanced AI Capabilities

- **Trend forecasting** (predict race times, injury risk)
- **Anomaly detection** (overtraining alerts, unusual patterns)
- **Training recommendations** (AI-generated workout plans)
- **Comparative analysis** (compare to similar users, age groups)

### 11.3 Mobile Applications

- **React Native** (iOS + Android)
- **Offline mode** (local SQLite cache)
- **Push notifications** (goal progress, insights)

### 11.4 Social Features

- **Share visualizations** (public URLs, social media cards)
- **Leaderboards** (opt-in, privacy-first)
- **Coaching mode** (invite coach to view your data)

---

## Appendix A: File Structure

**NOTE:** Complete folder structure should be created from day one (Phase 1), even if many folders start empty. This follows CliniCraft's well-organized monorepo pattern.

```
selflytics/
├── backend/
│   ├── app/
│   │   ├── auth/                 # Authentication service (Phase 1)
│   │   │   ├── __init__.py
│   │   │   ├── jwt_handler.py
│   │   │   └── password.py
│   │   ├── db/                   # Firestore abstraction (Phase 1)
│   │   │   ├── __init__.py
│   │   │   └── firestore.py
│   │   ├── middleware/           # Telemetry, CORS, rate limiting (Phase 1)
│   │   │   ├── __init__.py
│   │   │   ├── telemetry.py
│   │   │   └── cors.py
│   │   ├── models/               # Pydantic data models (Phase 1+)
│   │   │   ├── __init__.py
│   │   │   ├── user.py          # Phase 1
│   │   │   ├── garmin.py        # Phase 2
│   │   │   ├── chat.py          # Phase 3
│   │   │   ├── visualization.py # Phase 4
│   │   │   └── goal.py          # Phase 5
│   │   ├── routers/              # API endpoints (Phase 1+)
│   │   │   ├── __init__.py
│   │   │   ├── auth.py          # Phase 1
│   │   │   ├── garmin.py        # Phase 2
│   │   │   ├── chat.py          # Phase 3
│   │   │   ├── visualizations.py # Phase 4
│   │   │   └── goals.py         # Phase 5
│   │   ├── services/             # Business logic (Phase 2+)
│   │   │   ├── __init__.py
│   │   │   ├── garmin_service.py     # Phase 2
│   │   │   ├── chat_service.py       # Phase 3
│   │   │   ├── visualization_service.py # Phase 4
│   │   │   └── goal_service.py       # Phase 5
│   │   ├── templates/            # Jinja2 templates (Phase 1+)
│   │   │   ├── base.html        # Phase 1
│   │   │   ├── login.html       # Phase 1
│   │   │   ├── register.html    # Phase 1
│   │   │   ├── dashboard.html   # Phase 1
│   │   │   ├── chat.html        # Phase 3
│   │   │   └── partials/        # Phase 1+
│   │   │       ├── nav.html
│   │   │       ├── messages.html     # Phase 3
│   │   │       └── activity_list.html # Phase 2
│   │   ├── prompts/              # AI system prompts (Phase 3+)
│   │   │   ├── __init__.py
│   │   │   ├── chat_agent.py    # Phase 3
│   │   │   └── goal_inference.py # Phase 5
│   │   ├── utils/                # Helpers (Phase 1+)
│   │   │   ├── __init__.py
│   │   │   ├── cache.py         # Phase 2
│   │   │   ├── redact.py        # Phase 1
│   │   │   └── cost_tracking.py # Phase 3
│   │   ├── main.py               # FastAPI app (Phase 1)
│   │   ├── config.py             # Pydantic Settings (Phase 1)
│   │   └── telemetry_config.py   # Telemetry setup (Phase 1)
│   ├── packages/
│   │   └── telemetry/            # Workspace package (Phase 1)
│   │       ├── src/
│   │       │   └── selflytics_telemetry/
│   │       │       ├── __init__.py
│   │       │       ├── exporters/
│   │       │       └── config.py
│   │       ├── tests/
│   │       └── pyproject.toml
│   ├── tests/                    # pytest tests (Phase 1+)
│   │   ├── unit/
│   │   │   ├── services/
│   │   │   ├── models/
│   │   │   └── utils/
│   │   ├── integration/
│   │   │   └── routers/
│   │   ├── e2e/
│   │   └── conftest.py
│   ├── .env.example              # Environment template (Phase 1)
│   ├── Dockerfile                # Multi-stage build (Phase 1)
│   ├── pyproject.toml            # uv workspace config (Phase 1)
│   └── README.md                 # Backend-specific docs (Phase 1)
├── infra/                        # Terraform infrastructure (Phase 1+)
│   ├── modules/
│   │   ├── cloud_run/
│   │   │   ├── main.tf
│   │   │   ├── variables.tf
│   │   │   └── outputs.tf
│   │   ├── cloud_run_preview/
│   │   ├── firestore/
│   │   ├── secrets/
│   │   ├── storage/              # GCS for visualizations
│   │   └── dns/                  # Custom domain setup (Phase 6)
│   ├── environments/
│   │   ├── dev/
│   │   │   ├── main.tf
│   │   │   ├── backend.tf
│   │   │   └── terraform.tfvars
│   │   └── prod/                 # Phase 6
│   │       ├── main.tf
│   │       └── terraform.tfvars
│   └── scripts/
│       ├── deploy.sh
│       ├── preview               # Preview CLI
│       ├── commands/             # Preview subcommands
│       └── lib/                  # Shared shell libraries
├── static/                       # Frontend assets (Phase 1+)
│   ├── css/
│   │   └── custom.css           # Minimal custom styles
│   ├── js/
│   │   └── app.js               # Optional Alpine.js components
│   └── images/
│       └── logo.svg
├── docs/                         # Documentation (created during exploration)
│   ├── SELFLYTICS_SPECIFICATION.md (this file)
│   ├── GARMIN_AGENTS_EXPLORATION.md
│   ├── REUSABLE_PATTERNS_GUIDE.md
│   ├── README.md
│   ├── reference/                # Architecture specs (Phase 1+)
│   ├── operations/               # Deployment runbooks (Phase 6)
│   ├── features/                 # Feature documentation (Phase 2+)
│   ├── development/              # Active WIP docs (Phase 1+)
│   └── templates/                # Spec/roadmap/phase templates (Phase 1)
├── scripts/                      # Root-level utility scripts (Phase 1+)
│   └── setup_local_dev.sh
├── .github/
│   └── workflows/                # CI/CD pipelines (Phase 1)
│       ├── ci.yml
│       ├── cd.yml
│       ├── preview.yml
│       └── preview-cleanup.yml
├── .claude/                      # Claude Code configuration (Phase 1)
│   └── CLAUDE.md                # Project-specific patterns
├── .env.example                  # Root environment template (Phase 1)
├── .pre-commit-config.yaml       # Pre-commit hooks (Phase 1)
├── .gitignore                    # Git ignore rules (Phase 1)
├── README.md                     # Project overview (Phase 1)
└── LICENSE                       # License file (Phase 1)
```

**Folder Creation Strategy:**
- Phase 1: Create ALL folders, add `__init__.py` to Python packages, add README.md placeholders
- Phases 2-6: Populate folders with actual implementation
- Benefits: Clear organization from start, prevents restructuring later, easier navigation

---

## Appendix B: Key Decisions & Rationale

### B.1 Why Pydantic-AI over smolagents?

**Rationale:**
- **Structured outputs:** Pydantic-AI enforces output schemas, reducing hallucinations
- **Multi-model support:** Easily switch between OpenAI, Claude, local models
- **Better async support:** Built for FastAPI, native async/await
- **Active development:** Pydantic team maintains it, frequent updates
- **Type safety:** Full Pydantic validation for inputs/outputs

**Migration effort:** ~3 days to rewrite 8 smolagents tools as Pydantic-AI tools

### B.2 Why Jinja2 + HTMX over React?

**Rationale:**
- **Simpler stack:** No build step, no npm, no bundler complexity
- **Server control:** Backend renders all HTML, easier to secure
- **SEO-friendly:** Pre-rendered HTML, no client-side routing issues
- **Progressive enhancement:** Works without JavaScript (accessibility)
- **Faster prototyping:** Copy CliniCraft patterns, iterate quickly

**Trade-offs:** Less rich client interactions (acceptable for chat-first UI)

### B.3 Why Cloud Run over Cloud Functions?

**Rationale:**
- **Stateless HTTP:** Chat API is request/response, perfect for Cloud Run
- **Better scaling:** Scales to zero, handles traffic spikes
- **Container flexibility:** Docker gives full control over environment
- **Cost efficiency:** Pay per 100ms request time, auto-scales down

**Trade-offs:** Not suitable for background jobs (use Cloud Tasks for async work)

### B.4 Why Firestore over Cloud SQL?

**Rationale:**
- **Serverless:** No database management, auto-scales
- **Document model:** Natural fit for user data, conversations, cached JSON
- **Real-time queries:** Native support for live updates (future feature)
- **Cost:** Free tier covers MVP, pay-per-operation beyond

**Trade-offs:** Less flexible querying than SQL (acceptable for key-value lookups)

---

## Next Steps

**Immediate Actions:**
1. ✅ Specification reviewed and clarified (domain, region, telemetry, structure, beta size)
2. Create GitHub repository for the project
3. Set up GCP project (`selflytics-prod`) and billing
4. Set up complete project structure (following CliniCraft organization)
5. Begin spike implementation (1 week)
6. Decision meeting after spike: Proceed to Phase 1 or pivot?

**Confirmed Requirements:**
- ✅ **Production domain:** selflytics.anbaricideas.com
- ✅ **GCP region:** australia-southeast1 (Sydney)
- ✅ **Telemetry:** Cloud Logging (same as CliniCraft)
- ✅ **Project structure:** Complete folder structure from day one (CliniCraft-based)
- ✅ **Beta user group:** ~10 users

---

**End of Specification**
