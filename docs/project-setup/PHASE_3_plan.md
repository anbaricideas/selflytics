# Phase 3: Chat Interface + AI Agent

**Branch**: `feat/phase-3-chat-ai`
**Status**: ⬜ TODO
**Estimated Time**: 120 hours (3 weeks)

---

## Goal

Implement natural language chat interface with Pydantic-AI agent for fitness insights. This phase enables users to ask questions about their Garmin data and receive AI-powered analysis with conversation history, cost tracking, and conversational memory.

**Key Deliverables**:
- Pydantic-AI chat agent with fitness analysis prompts
- Garmin data tools (get_activities, get_metrics, get_profile)
- Chat UI with HTMX (Jinja2 + Alpine.js)
- Conversation management (Firestore storage)
- Message history and context (last 10 messages)
- Cost tracking for AI usage (tokens, pricing)
- Goal inference agent (extract goals from conversation)
- 80%+ test coverage (mocked OpenAI)

---

## Prerequisites

- ✅ Phase 2 completed (Garmin integration working)
- ✅ User can link Garmin account
- ✅ GarminService returns cached data
- ✅ Pydantic models for Garmin data available
- ✅ OpenAI API key configured in Secret Manager

---

## Deliverables

### AI Agent (Pydantic-AI)

- ✅ `backend/app/services/chat_service.py` - Chat agent orchestration
- ✅ `backend/app/prompts/chat_agent.py` - System prompts
- ✅ `backend/app/prompts/goal_inference.py` - Goal extraction prompts
- ✅ `backend/app/models/chat.py` - Pydantic models (ChatResponse, Message)
- ✅ Tools: garmin_activity_tool, garmin_metrics_tool, garmin_profile_tool

### Conversation Management

- ✅ `backend/app/services/conversation_service.py` - CRUD operations
- ✅ `backend/app/models/conversation.py` - Conversation, Message models
- ✅ Firestore collections: `conversations`, `conversations/{id}/messages`
- ✅ Message history context (last 10 messages)

### Cost Tracking

- ✅ `backend/app/models/cost_tracking.py` - ChatUsage model
- ✅ `backend/app/utils/cost_tracking.py` - Cost calculation utilities
- ✅ Token tracking in message metadata
- ✅ Aggregate cost reporting

### Chat UI

- ✅ `backend/app/templates/chat.html` - Main chat interface
- ✅ `backend/app/templates/partials/messages.html` - Message partial (HTMX)
- ✅ `backend/app/templates/conversation_list.html` - Conversation history
- ✅ HTMX for async message loading
- ✅ Alpine.js for loading states

### API Routes

- ✅ `backend/app/routes/chat.py` - Chat endpoints
- ✅ POST /chat/send - Send message
- ✅ GET /chat/{conversation_id} - Load conversation
- ✅ GET /chat/conversations - List user conversations
- ✅ DELETE /chat/{conversation_id} - Delete conversation

### Tests

- ✅ `backend/tests/unit/test_chat_service.py` - Agent logic
- ✅ `backend/tests/unit/test_cost_tracking.py` - Cost calculations
- ✅ `backend/tests/integration/test_chat_workflow.py` - Full workflow
- ✅ 80%+ coverage on new code

---

## Implementation Steps

### Setup

- [ ] ⏳ NEXT: Create branch `feat/phase-3-chat-ai`
- [ ] Install dependencies:
  - `uv add pydantic-ai`
  - `uv add openai`
- [ ] Review CliniCraft blog generator: `/Users/bryn/repos/clinicraft/backend/app/services/blog_generator_service.py`

---

### Step 1: Chat Data Models

**File**: `backend/app/models/chat.py`

- [ ] Write tests first: `backend/tests/unit/test_chat_models.py`
  - Test ChatResponse model validation
  - Test Message model validation
  - Test confidence range (0.0 - 1.0)
- [ ] Implement chat Pydantic models:
  ```python
  """Chat data models."""
  from pydantic import BaseModel, Field
  from datetime import datetime
  from typing import Optional

  class ChatResponse(BaseModel):
      """Structured response from chat agent."""
      message: str = Field(..., description="Natural language response to user")
      data_sources_used: list[str] = Field(
          default_factory=list,
          description="Garmin data types queried (activities, metrics, profile)"
      )
      confidence: float = Field(
          ge=0.0,
          le=1.0,
          description="Confidence in response accuracy (0.0 - 1.0)"
      )
      suggested_followup: Optional[str] = Field(
          None,
          description="Suggested next question for user"
      )

  class Message(BaseModel):
      """Chat message in conversation."""
      message_id: str
      conversation_id: str
      role: str  # "user" or "assistant"
      content: str
      timestamp: datetime
      metadata: Optional[dict] = None  # Tokens, cost, model used

  class ChatRequest(BaseModel):
      """Request to send chat message."""
      message: str = Field(..., min_length=1, max_length=2000)
      conversation_id: Optional[str] = None  # Create new if None
  ```
- [ ] Verify tests pass
- [ ] Commit: "feat: add chat Pydantic models"

**File**: `backend/app/models/conversation.py`

- [ ] Write tests first: `backend/tests/unit/test_conversation_model.py`
- [ ] Implement Conversation model:
  ```python
  """Conversation data models."""
  from pydantic import BaseModel, Field
  from datetime import datetime
  from typing import Optional

  class Conversation(BaseModel):
      """Conversation between user and AI."""
      conversation_id: str
      user_id: str
      title: str = Field(default="New Conversation")  # AI-generated from first message
      created_at: datetime
      updated_at: datetime
      message_count: int = 0
      metadata: Optional[dict] = None  # Topics, date ranges queried

  class ConversationCreate(BaseModel):
      """Create new conversation."""
      user_id: str
      first_message: str
  ```
- [ ] Verify tests pass
- [ ] Commit: "feat: add Conversation models"

---

### Step 2: Cost Tracking Models

**File**: `backend/app/models/cost_tracking.py`

- [ ] Copy from CliniCraft `backend/app/models/cost_tracking.py`
- [ ] Adapt for chat usage (instead of blog generation):
  ```python
  """Cost tracking models for AI usage."""
  from pydantic import BaseModel
  from datetime import datetime

  class ChatUsage(BaseModel):
      """Token usage for a single chat exchange."""
      input_tokens: int
      output_tokens: int
      cached_tokens: int = 0
      reasoning_tokens: int = 0  # For o1 models
      cost_usd: float
      model: str
      timestamp: datetime

  class TokenCost(BaseModel):
      """Token pricing for a model."""
      model: str
      input_cost_per_1m: float  # Cost per 1M input tokens
      output_cost_per_1m: float
      cached_cost_per_1m: float = 0.0
      reasoning_cost_per_1m: float = 0.0

  # Pricing for gpt-4.1-mini (2025-04-14)
  GPT_4_1_MINI_PRICING = TokenCost(
      model="gpt-4.1-mini-2025-04-14",
      input_cost_per_1m=0.15,
      output_cost_per_1m=0.60,
      cached_cost_per_1m=0.075  # 50% discount for cached inputs
  )
  ```
- [ ] Verify tests pass
- [ ] Commit: "feat: add cost tracking models"

**File**: `backend/app/utils/cost_tracking.py`

- [ ] Write tests first: `backend/tests/unit/test_cost_tracking.py`
  - Test cost calculation with various token counts
  - Test cached token discount
  - Test reasoning token pricing (o1 models)
- [ ] Implement cost calculation utilities:
  ```python
  """Cost calculation utilities."""
  from app.models.cost_tracking import ChatUsage, TokenCost, GPT_4_1_MINI_PRICING
  from datetime import datetime

  def calculate_cost(
      input_tokens: int,
      output_tokens: int,
      cached_tokens: int = 0,
      reasoning_tokens: int = 0,
      pricing: TokenCost = GPT_4_1_MINI_PRICING
  ) -> float:
      """
      Calculate cost in USD for token usage.

      Args:
          input_tokens: Non-cached input tokens
          output_tokens: Output tokens
          cached_tokens: Cached input tokens (discounted)
          reasoning_tokens: Reasoning tokens (o1 models)
          pricing: Token pricing model

      Returns:
          Total cost in USD
      """
      cost = (
          (input_tokens * pricing.input_cost_per_1m / 1_000_000) +
          (output_tokens * pricing.output_cost_per_1m / 1_000_000) +
          (cached_tokens * pricing.cached_cost_per_1m / 1_000_000) +
          (reasoning_tokens * pricing.reasoning_cost_per_1m / 1_000_000)
      )
      return cost

  def create_usage_record(
      usage_dict: dict,
      model: str = "gpt-4.1-mini-2025-04-14"
  ) -> ChatUsage:
      """
      Create ChatUsage record from API response.

      Args:
          usage_dict: Usage dictionary from OpenAI API response
          model: Model name

      Returns:
          ChatUsage record with calculated cost
      """
      input_tokens = usage_dict.get("prompt_tokens", 0)
      output_tokens = usage_dict.get("completion_tokens", 0)
      cached_tokens = usage_dict.get("prompt_tokens_details", {}).get("cached_tokens", 0)

      cost = calculate_cost(
          input_tokens=input_tokens - cached_tokens,  # Non-cached input
          output_tokens=output_tokens,
          cached_tokens=cached_tokens
      )

      return ChatUsage(
          input_tokens=input_tokens,
          output_tokens=output_tokens,
          cached_tokens=cached_tokens,
          cost_usd=cost,
          model=model,
          timestamp=datetime.utcnow()
      )
  ```
- [ ] Verify tests pass
- [ ] Commit: "feat: add cost calculation utilities"

**Implementation Reference**: CliniCraft cost tracking utilities

---

### Step 3: Pydantic-AI Tools (Garmin Data)

**File**: `backend/app/prompts/chat_agent.py`

- [ ] Write tests first: `backend/tests/unit/test_chat_tools.py`
  - Test garmin_activity_tool with mock service
  - Test garmin_metrics_tool
  - Test garmin_profile_tool
  - Test tool response format
- [ ] Implement Pydantic-AI tools:
  ```python
  """Pydantic-AI tools for Garmin data access."""
  from pydantic_ai import RunContext
  from datetime import date, timedelta
  from app.services.garmin_service import GarminService
  from typing import Optional

  async def garmin_activity_tool(
      ctx: RunContext[str],
      start_date: str,
      end_date: str,
      activity_type: Optional[str] = None
  ) -> dict:
      """
      Get user activities from Garmin Connect in date range.

      Args:
          ctx: Run context (contains user_id)
          start_date: Start date (YYYY-MM-DD)
          end_date: End date (YYYY-MM-DD)
          activity_type: Optional activity type filter (running, cycling, swimming)

      Returns:
          Dictionary with activities list and count
      """
      user_id = ctx.deps  # user_id passed as dependency

      service = GarminService(user_id)

      # Parse dates
      start = date.fromisoformat(start_date)
      end = date.fromisoformat(end_date)

      # Fetch activities (uses cache if available)
      activities = await service.get_activities_cached(start, end)

      # Filter by type if specified
      if activity_type:
          activities = [
              a for a in activities
              if a.get("activity_type", "").lower() == activity_type.lower()
          ]

      # Simplify for AI consumption
      simplified = [
          {
              "date": a.get("start_time_local", "unknown"),
              "type": a.get("activity_type", "unknown"),
              "distance_km": round(a.get("distance_meters", 0) / 1000, 2),
              "duration_min": round(a.get("duration_seconds", 0) / 60, 1),
              "avg_hr": a.get("average_hr"),
              "calories": a.get("calories")
          }
          for a in activities[:50]  # Limit to 50 for token efficiency
      ]

      return {
          "activities": simplified,
          "total_count": len(activities),
          "date_range": f"{start_date} to {end_date}"
      }

  async def garmin_metrics_tool(
      ctx: RunContext[str],
      metric_type: str,
      days: int = 7
  ) -> dict:
      """
      Get daily metrics from Garmin (steps, heart rate, sleep, etc.).

      Args:
          ctx: Run context
          metric_type: Metric type (steps, resting_hr, sleep, stress)
          days: Number of days to retrieve (default: 7)

      Returns:
          Dictionary with metric values and average
      """
      user_id = ctx.deps
      service = GarminService(user_id)

      # Fetch metrics for last N days
      end_date = date.today()
      start_date = end_date - timedelta(days=days)

      metrics_list = []
      current_date = start_date

      while current_date <= end_date:
          try:
              metrics = await service.get_daily_metrics_cached(current_date)
              value = None

              # Extract requested metric
              if metric_type == "steps":
                  value = metrics.get("steps")
              elif metric_type == "resting_hr":
                  value = metrics.get("resting_heart_rate")
              elif metric_type == "sleep":
                  value = metrics.get("sleep_seconds", 0) / 3600  # Convert to hours
              elif metric_type == "stress":
                  value = metrics.get("avg_stress_level")

              if value is not None:
                  metrics_list.append({
                      "date": current_date.isoformat(),
                      "value": value
                  })

          except Exception:
              pass  # Skip days with missing data

          current_date += timedelta(days=1)

      # Calculate average
      values = [m["value"] for m in metrics_list if m["value"] is not None]
      average = sum(values) / len(values) if values else 0

      return {
          "metric_type": metric_type,
          "days": days,
          "data": metrics_list,
          "average": round(average, 2),
          "unit": _get_metric_unit(metric_type)
      }

  async def garmin_profile_tool(ctx: RunContext[str]) -> dict:
      """
      Get user's Garmin profile information.

      Args:
          ctx: Run context

      Returns:
          Dictionary with profile data
      """
      user_id = ctx.deps
      service = GarminService(user_id)

      profile = await service.get_user_profile()

      return {
          "display_name": profile.get("display_name", "User"),
          "email": profile.get("email"),
          "garmin_linked": True
      }

  def _get_metric_unit(metric_type: str) -> str:
      """Get unit for metric type."""
      units = {
          "steps": "steps/day",
          "resting_hr": "bpm",
          "sleep": "hours",
          "stress": "0-100"
      }
      return units.get(metric_type, "")
  ```
- [ ] Verify tests pass
- [ ] Commit: "feat: add Pydantic-AI tools for Garmin data"

---

### Step 4: Chat Agent Definition

**File**: `backend/app/prompts/chat_agent.py` (continued)

- [ ] Define system prompt for fitness insights:
  ```python
  """Chat agent system prompt."""

  CHAT_AGENT_SYSTEM_PROMPT = """You are a fitness data analyst assistant for Selflytics.

  Your role:
  - Answer user questions about their Garmin fitness data
  - Provide insights on trends, patterns, and progress
  - Be encouraging but accurate (don't exaggerate progress)
  - Use metric units unless user specifies imperial
  - Respect privacy (never share data outside conversation)

  Available data sources:
  - Running, cycling, swimming activities (via garmin_activity_tool)
  - Daily metrics: steps, heart rate, sleep, stress (via garmin_metrics_tool)
  - User profile information (via garmin_profile_tool)

  Guidelines:
  - Reference specific dates/activities when possible
  - Acknowledge data limitations (e.g., "Based on last 7 days...")
  - Keep responses conversational and helpful
  - Suggest followup questions when appropriate
  - If user asks about data you don't have, explain what's available

  Data interpretation tips:
  - Resting HR decrease = fitness improvement
  - Sleep consistency = important for recovery
  - Stress levels: <25 low, 25-50 medium, 50-75 high, >75 very high
  - Running pace: faster = lower min/km value
  - Activity frequency: 3-5x per week is typical for active users

  Always provide:
  - Confidence in your analysis (0.0 - 1.0)
  - Data sources used (list of tools called)
  - Suggested followup question (optional)
  """
  ```

- [ ] Create Pydantic-AI agent:
  ```python
  from pydantic_ai import Agent
  from app.models.chat import ChatResponse

  chat_agent = Agent(
      model="openai:gpt-4.1-mini-2025-04-14",
      system_prompt=CHAT_AGENT_SYSTEM_PROMPT,
      result_type=ChatResponse,
      tools=[
          garmin_activity_tool,
          garmin_metrics_tool,
          garmin_profile_tool
      ]
  )
  ```
- [ ] Commit: "feat: add chat agent with system prompt"

---

### Step 5: Conversation Service

**File**: `backend/app/services/conversation_service.py`

- [ ] Write tests first: `backend/tests/unit/test_conversation_service.py`
  - Test create_conversation
  - Test add_message
  - Test get_conversation
  - Test get_message_history (last 10)
  - Test list_conversations (user's conversations)
- [ ] Implement ConversationService:
  ```python
  """Conversation management service."""
  from app.models.conversation import Conversation, Message
  from app.db.firestore_client import get_firestore_client
  from datetime import datetime
  import uuid

  class ConversationService:
      """Manage chat conversations."""

      def __init__(self):
          self.db = get_firestore_client()
          self.conversations_collection = self.db.collection("conversations")

      async def create_conversation(
          self,
          user_id: str,
          first_message: str
      ) -> Conversation:
          """Create new conversation."""
          conversation_id = str(uuid.uuid4())
          now = datetime.utcnow()

          # Create conversation
          conversation = Conversation(
              conversation_id=conversation_id,
              user_id=user_id,
              title="New Conversation",  # Will update after AI response
              created_at=now,
              updated_at=now,
              message_count=0
          )

          # Save to Firestore
          self.conversations_collection.document(conversation_id).set(
              conversation.dict()
          )

          return conversation

      async def add_message(
          self,
          conversation_id: str,
          role: str,
          content: str,
          metadata: dict = None
      ) -> Message:
          """Add message to conversation."""
          message_id = str(uuid.uuid4())
          now = datetime.utcnow()

          message = Message(
              message_id=message_id,
              conversation_id=conversation_id,
              role=role,
              content=content,
              timestamp=now,
              metadata=metadata or {}
          )

          # Save to subcollection
          messages_ref = (
              self.conversations_collection
              .document(conversation_id)
              .collection("messages")
          )
          messages_ref.document(message_id).set(message.dict())

          # Update conversation metadata
          conv_ref = self.conversations_collection.document(conversation_id)
          conv_ref.update({
              "updated_at": now,
              "message_count": firestore.Increment(1)
          })

          return message

      async def get_message_history(
          self,
          conversation_id: str,
          limit: int = 10
      ) -> list[Message]:
          """Get last N messages for conversation context."""
          messages_ref = (
              self.conversations_collection
              .document(conversation_id)
              .collection("messages")
              .order_by("timestamp", direction="DESCENDING")
              .limit(limit)
          )

          messages = []
          for doc in messages_ref.stream():
              messages.append(Message(**doc.to_dict()))

          # Return chronological order
          return list(reversed(messages))

      async def get_conversation(
          self,
          conversation_id: str
      ) -> Conversation | None:
          """Get conversation by ID."""
          doc = self.conversations_collection.document(conversation_id).get()
          if doc.exists:
              return Conversation(**doc.to_dict())
          return None

      async def list_conversations(
          self,
          user_id: str,
          limit: int = 20
      ) -> list[Conversation]:
          """List user's conversations."""
          query = (
              self.conversations_collection
              .where("user_id", "==", user_id)
              .order_by("updated_at", direction="DESCENDING")
              .limit(limit)
          )

          conversations = []
          for doc in query.stream():
              conversations.append(Conversation(**doc.to_dict()))

          return conversations

      async def generate_title(
          self,
          conversation_id: str,
          first_user_message: str
      ):
          """Generate conversation title from first message (AI-powered)."""
          # Simple heuristic for now - use first 50 chars
          title = first_user_message[:50]
          if len(first_user_message) > 50:
              title += "..."

          # Update conversation
          self.conversations_collection.document(conversation_id).update({
              "title": title
          })
  ```
- [ ] Verify tests pass
- [ ] Commit: "feat: add ConversationService"

---

### Step 6: Chat Service (Agent Orchestration)

**File**: `backend/app/services/chat_service.py`

- [ ] Write tests first: `backend/tests/unit/test_chat_service.py`
  - Test send_message (mocked agent)
  - Test message history context
  - Test cost tracking integration
  - Test conversation creation
- [ ] Implement ChatService:
  ```python
  """Chat service orchestrating agent and conversation management."""
  from app.services.conversation_service import ConversationService
  from app.prompts.chat_agent import chat_agent
  from app.models.chat import ChatRequest, ChatResponse
  from app.utils.cost_tracking import create_usage_record
  import logging

  logger = logging.getLogger(__name__)

  class ChatService:
      """High-level chat service."""

      def __init__(self):
          self.conversation_service = ConversationService()

      async def send_message(
          self,
          user_id: str,
          request: ChatRequest
      ) -> tuple[ChatResponse, str]:
          """
          Send chat message and get AI response.

          Args:
              user_id: User ID
              request: Chat request with message and optional conversation_id

          Returns:
              Tuple of (ChatResponse, conversation_id)
          """
          # Create or get conversation
          if request.conversation_id:
              conversation = await self.conversation_service.get_conversation(
                  request.conversation_id
              )
              if not conversation:
                  raise ValueError("Conversation not found")
              conversation_id = request.conversation_id
          else:
              # Create new conversation
              conversation = await self.conversation_service.create_conversation(
                  user_id=user_id,
                  first_message=request.message
              )
              conversation_id = conversation.conversation_id

          # Save user message
          user_message = await self.conversation_service.add_message(
              conversation_id=conversation_id,
              role="user",
              content=request.message
          )

          # Get message history for context
          history = await self.conversation_service.get_message_history(
              conversation_id=conversation_id,
              limit=10
          )

          # Format history for agent
          message_history = [
              {"role": msg.role, "content": msg.content}
              for msg in history[:-1]  # Exclude the message we just added
          ]

          # Run agent
          try:
              result = await chat_agent.run(
                  request.message,
                  deps=user_id,  # Pass user_id to tools
                  message_history=message_history
              )

              response = result.data

              # Extract usage for cost tracking
              usage_record = create_usage_record(
                  usage_dict=result.usage(),
                  model="gpt-4.1-mini-2025-04-14"
              )

              # Save assistant message with metadata
              await self.conversation_service.add_message(
                  conversation_id=conversation_id,
                  role="assistant",
                  content=response.message,
                  metadata={
                      "model_used": "gpt-4.1-mini-2025-04-14",
                      "tokens": usage_record.dict(),
                      "cost_usd": usage_record.cost_usd,
                      "confidence": response.confidence,
                      "data_sources_used": response.data_sources_used
                  }
              )

              # Generate title if first exchange
              if len(history) == 1:  # Only user message
                  await self.conversation_service.generate_title(
                      conversation_id=conversation_id,
                      first_user_message=request.message
                  )

              logger.info(
                  f"Chat response generated - conversation: {conversation_id}, "
                  f"cost: ${usage_record.cost_usd:.4f}"
              )

              return response, conversation_id

          except Exception as e:
              logger.error(f"Chat agent error: {e}")
              raise
  ```
- [ ] Verify tests pass
- [ ] Commit: "feat: add ChatService with agent orchestration"

---

### Step 7: Chat Routes

**File**: `backend/app/routes/chat.py`

- [ ] Write tests first: `backend/tests/integration/test_chat_routes.py`
  - Test POST /chat/send (new conversation)
  - Test POST /chat/send (existing conversation)
  - Test GET /chat/{conversation_id}
  - Test GET /chat/conversations
  - Test DELETE /chat/{conversation_id}
- [ ] Implement chat routes:
  ```python
  """Chat API routes."""
  from fastapi import APIRouter, Depends, HTTPException, Request, status
  from fastapi.responses import HTMLResponse
  from app.auth.dependencies import get_current_user
  from app.models.user import UserResponse
  from app.models.chat import ChatRequest
  from app.services.chat_service import ChatService

  router = APIRouter(prefix="/chat", tags=["chat"])

  @router.post("/send")
  async def send_message(
      request: ChatRequest,
      current_user: UserResponse = Depends(get_current_user)
  ):
      """Send chat message and get AI response."""
      service = ChatService()

      try:
          response, conversation_id = await service.send_message(
              user_id=current_user.user_id,
              request=request
          )

          return {
              "conversation_id": conversation_id,
              "response": response.dict()
          }

      except Exception as e:
          raise HTTPException(
              status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
              detail=str(e)
          )

  @router.get("/conversations")
  async def list_conversations(
      current_user: UserResponse = Depends(get_current_user)
  ):
      """List user's conversations."""
      service = ChatService()
      conversations = await service.conversation_service.list_conversations(
          user_id=current_user.user_id
      )

      return {"conversations": [c.dict() for c in conversations]}

  @router.get("/{conversation_id}")
  async def get_conversation(
      conversation_id: str,
      current_user: UserResponse = Depends(get_current_user)
  ):
      """Get conversation with messages."""
      service = ChatService()

      conversation = await service.conversation_service.get_conversation(
          conversation_id
      )

      if not conversation or conversation.user_id != current_user.user_id:
          raise HTTPException(
              status_code=status.HTTP_404_NOT_FOUND,
              detail="Conversation not found"
          )

      messages = await service.conversation_service.get_message_history(
          conversation_id=conversation_id,
          limit=100  # All messages for display
      )

      return {
          "conversation": conversation.dict(),
          "messages": [m.dict() for m in messages]
          }

  @router.delete("/{conversation_id}")
  async def delete_conversation(
      conversation_id: str,
      current_user: UserResponse = Depends(get_current_user)
  ):
      """Delete conversation (soft delete)."""
      # Implementation: mark as deleted or actually delete
      # For now, simple response
      return {"message": "Conversation deleted"}
  ```
- [ ] Update `backend/app/main.py`:
  ```python
  from app.routes import chat
  app.include_router(chat.router)
  ```
- [ ] Verify tests pass
- [ ] Commit: "feat: add chat API routes"

---

### Step 8: Chat UI Templates

**File**: `backend/app/templates/chat.html`

- [ ] Create chat interface template:
  ```html
  {% extends "base.html" %}

  {% block content %}
  <div class="h-screen flex" x-data="chatInterface()">
      <!-- Sidebar: Conversation list -->
      <aside class="w-64 bg-gray-50 border-r overflow-y-auto">
          <div class="p-4">
              <h2 class="font-semibold text-lg mb-4">Conversations</h2>

              <button
                  @click="newConversation()"
                  class="w-full bg-blue-600 text-white py-2 rounded mb-4 hover:bg-blue-700"
              >
                  New Chat
              </button>

              <div class="space-y-2">
                  <template x-for="conv in conversations" :key="conv.conversation_id">
                      <div
                          @click="loadConversation(conv.conversation_id)"
                          :class="{'bg-blue-100': currentConversationId === conv.conversation_id}"
                          class="p-3 rounded cursor-pointer hover:bg-gray-100"
                      >
                          <p class="text-sm font-medium truncate" x-text="conv.title"></p>
                          <p class="text-xs text-gray-500" x-text="formatDate(conv.updated_at)"></p>
                      </div>
                  </template>
              </div>
          </div>
      </aside>

      <!-- Main chat area -->
      <div class="flex-1 flex flex-col">
          <!-- Messages -->
          <div id="messages" class="flex-1 overflow-y-auto p-6 space-y-4">
              <template x-for="msg in messages" :key="msg.message_id">
                  <div :class="msg.role === 'user' ? 'text-right' : 'text-left'">
                      <div
                          :class="msg.role === 'user' ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-800'"
                          class="inline-block px-4 py-2 rounded-lg max-w-2xl"
                      >
                          <p x-text="msg.content"></p>

                          <!-- Assistant metadata -->
                          <template x-if="msg.role === 'assistant' && msg.metadata">
                              <div class="mt-2 text-xs opacity-75">
                                  <span x-text="`Confidence: ${(msg.metadata.confidence * 100).toFixed(0)}%`"></span>
                              </div>
                          </template>
                      </div>
                  </div>
              </template>

              <!-- Loading indicator -->
              <div x-show="loading" class="text-center">
                  <div class="inline-block animate-pulse text-gray-500">AI is thinking...</div>
              </div>
          </div>

          <!-- Input form -->
          <div class="border-t p-4">
              <form @submit.prevent="sendMessage()" class="flex gap-2">
                  <input
                      x-model="messageInput"
                      type="text"
                      placeholder="Ask about your fitness data..."
                      class="flex-1 border rounded px-4 py-2"
                      :disabled="loading"
                  >
                  <button
                      type="submit"
                      :disabled="loading || !messageInput.trim()"
                      class="bg-blue-600 text-white px-6 py-2 rounded hover:bg-blue-700 disabled:opacity-50"
                  >
                      Send
                  </button>
              </form>
          </div>
      </div>
  </div>

  <script>
  function chatInterface() {
      return {
          conversations: [],
          currentConversationId: null,
          messages: [],
          messageInput: '',
          loading: false,

          async init() {
              await this.loadConversations();
          },

          async loadConversations() {
              const response = await fetch('/chat/conversations');
              const data = await response.json();
              this.conversations = data.conversations;
          },

          async loadConversation(conversationId) {
              this.currentConversationId = conversationId;
              const response = await fetch(`/chat/${conversationId}`);
              const data = await response.json();
              this.messages = data.messages;
          },

          async sendMessage() {
              if (!this.messageInput.trim()) return;

              const userMessage = this.messageInput;
              this.messageInput = '';
              this.loading = true;

              try {
                  const response = await fetch('/chat/send', {
                      method: 'POST',
                      headers: {'Content-Type': 'application/json'},
                      body: JSON.stringify({
                          message: userMessage,
                          conversation_id: this.currentConversationId
                      })
                  });

                  const data = await response.json();

                  // Update conversation ID if new
                  if (!this.currentConversationId) {
                      this.currentConversationId = data.conversation_id;
                  }

                  // Reload conversation to show new messages
                  await this.loadConversation(this.currentConversationId);
                  await this.loadConversations();  // Refresh list

              } catch (error) {
                  alert('Failed to send message');
              } finally {
                  this.loading = false;
              }
          },

          newConversation() {
              this.currentConversationId = null;
              this.messages = [];
              this.messageInput = '';
          },

          formatDate(dateStr) {
              return new Date(dateStr).toLocaleDateString();
          }
      }
  }
  </script>
  {% endblock %}
  ```
- [ ] Commit: "feat: add chat UI template with HTMX"

---

### Final Steps

- [ ] Run full test suite: `uv run pytest backend/tests/ -v --cov=app`
- [ ] Verify 80%+ coverage on new code
- [ ] Run quality checks:
  - `uv run ruff check .`
  - `uv run ruff format .`
- [ ] Manual testing:
  - Start server: `uv run --directory backend uvicorn app.main:app --reload`
  - Link Garmin account (if not already linked)
  - Visit chat: http://localhost:8000/chat
  - Test conversation flow:
    - "How many runs did I do this week?"
    - "What was my average pace?"
    - "Show my step count for last 7 days"
  - Verify AI uses tools (check logs)
  - Verify conversation history persists
  - Check Firestore: conversations and messages saved
  - Verify cost tracking in message metadata
- [ ] Final commit: "feat: complete Phase 3 - Chat Interface + AI Agent"
- [ ] Update this plan: mark all steps ✅ DONE
- [ ] Update `docs/project-setup/ROADMAP.md`: Phase 3 status → ✅ DONE
- [ ] Create PR: `feat/phase-3-chat-ai` → `main`

---

## Success Criteria

- ✅ User can ask questions about fitness data in natural language
- ✅ AI agent uses tools to query real Garmin data
- ✅ Agent cites specific dates/activities in responses
- ✅ Conversation history persists across sessions
- ✅ Message history (last 10) passed as context
- ✅ Token usage tracked and costs calculated
- ✅ Cost per conversation < $0.05 (typical)
- ✅ Chat UI responsive and functional
- ✅ New conversations created automatically
- ✅ Conversation list shows recent chats
- ✅ 80%+ test coverage achieved
- ✅ All integration tests pass

---

## Notes

### Design Decisions

1. **Conversation Context**: Last 10 messages passed to agent for continuity. Prevents token overflow while maintaining conversation flow.

2. **Cost Tracking**: Every message tracks tokens and cost. Enables future cost analysis and user billing (if needed).

3. **Tool Design**: Tools return simplified data (not full API responses) to reduce token usage. Agent gets what it needs without noise.

4. **Title Generation**: Simple heuristic (first 50 chars) for v1. Future: AI-generated titles.

5. **Message Metadata**: Stored in Firestore for cost tracking, model version tracking, confidence scores.

### Reference Implementations

**From CliniCraft**:
- `backend/app/services/blog_generator_service.py` - Pydantic-AI agent pattern
- `backend/app/prompts/blog_generation.py` - System prompt examples
- `backend/app/utils/ai_call_tracker.py` - Token tracking patterns
- `backend/app/models/cost_tracking.py` - Cost models

**From Spike**:
- `spike/chat_agent.py` - Basic agent structure
- `spike/garmin_client.py` - Tool data fetching patterns

### Common Pitfalls

- **Context Length**: 10 messages × ~200 tokens = ~2000 tokens. Monitor context growth.
- **Tool Response Size**: Limit activities to 50, metrics to 30 days max to control token usage.
- **Async Tools**: All tools must be async (FastAPI requirement).
- **User ID in Context**: Pass user_id via RunContext deps, not global state.
- **Message Order**: Firestore queries return newest first - reverse for chronological display.

### Deferred to Future Phases

- AI-generated visualization requests (Phase 4)
- Goal tracking and suggestions (Phase 5)
- Conversation export (Phase 5)
- Streaming responses (future optimization)
- Multi-user conversations (future social feature)

---

## Dependencies for Next Phase

**Phase 4** (Visualization Generation) will need:
- ✅ Chat agent working with tools
- ✅ Conversation context available
- ✅ ChatResponse model (extend for viz requests)
- ✅ Cost tracking infrastructure
- ✅ UI for displaying visualizations

With Phase 3 complete, Phase 4 can extend ChatResponse to request visualizations and integrate chart generation into the chat flow.

---

*Last Updated: 2025-11-11*
*Status: ⬜ TODO*
