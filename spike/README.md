# Selflytics Spike: Technical Validation

**Status**: ✅ Complete
**Date**: 2025-11-11
**Duration**: ~8 hours (1 dev session)

## Overview

This spike validates core technical assumptions for the Selflytics project before committing to full implementation:

1. **Pydantic-AI** can effectively provide fitness insights from Garmin data
2. **Garmin OAuth + MFA** flow works reliably with the garth library
3. **Visualization generation** meets performance requirements (<3 seconds)
4. **FastAPI async patterns** integrate smoothly with garth library

## What Was Built

A minimal proof-of-concept application with:

- **FastAPI server** with health check, chat, and visualization endpoints
- **Pydantic-AI chat agent** with tools for querying Garmin data
- **Garmin client** with OAuth authentication and MFA support
- **Visualization generator** using matplotlib for chart creation
- **Integration tests** to validate core workflows

## Quick Start

### Prerequisites

- Python 3.12+
- uv package manager
- Garmin Connect account (for testing OAuth flow)
- OpenAI API key (optional - TestModel works without it)

### Installation

```bash
# Install dependencies
uv sync

# Copy environment template
cp spike/.env.example spike/.env

# Edit .env and add your credentials (optional for basic testing)
```

### Running the Server

```bash
# Start FastAPI server
uv run --package selflytics-spike uvicorn spike.main:app --reload --host 127.0.0.1 --port 8000
```

### Testing Endpoints

```bash
# Health check
curl http://localhost:8000/health

# Generate visualization (test endpoint)
curl -X POST http://localhost:8000/generate-viz

# View generated chart
open http://localhost:8000/viz/{viz_id}

# Chat endpoint (requires OPENAI_API_KEY or returns TestModel output)
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "How am I doing?", "user_id": "test-user"}'
```

### Running Tests

```bash
# Run all integration tests
uv run --package selflytics-spike pytest spike/tests/ -v

# Results: 3 passed, 1 skipped
```

## Architecture

```
spike/
├── main.py                 # FastAPI application
├── chat_agent.py           # Pydantic-AI agent with tools
├── garmin_client.py        # Garmin Connect integration
├── viz_generator.py        # Matplotlib chart generation
├── cache/                  # Token storage + generated charts
├── tests/
│   └── test_integration.py # Integration tests
├── pyproject.toml          # Dependencies
└── README.md              # This file
```

## Key Findings

### ✅ Pydantic-AI Agent

**Validation**: Agent successfully provides structured responses with tools

- **Model**: OpenAI GPT-4o-mini (falls back to TestModel without API key)
- **Tools**: `get_activities_tool`, `get_metrics_tool`
- **Output**: Structured `ChatResponse` with message, sources, confidence
- **Migration Complexity**: **Low** - straightforward transition from smolagents

**Example Response** (with real API key):
```json
{
  "message": "Based on your activities, you've logged 2 runs this week...",
  "data_sources_used": ["activities"],
  "confidence": 0.9,
  "suggested_followup": "Would you like to see your pace trends?"
}
```

### ✅ Garmin Integration

**Validation**: OAuth + MFA flow works reliably with garth library

- **Authentication**: Username/password with MFA support
- **Token Storage**: Persistent tokens in `spike/cache/garmin_tokens`
- **Token Resume**: Successfully reloads existing sessions
- **MFA Flow**: Interactive console input (for spike simplicity)
- **Data Fetching**: Activities and daily metrics retrieved successfully
- **FastAPI Compatibility**: ✅ Async patterns work smoothly

**Test Results**:
- OAuth flow completed successfully (manual testing)
- Token save/load cycle validated
- MFA prompt appeared and completed (when enabled)
- 1 week of activities fetched without errors

### ✅ Visualization Generation

**Validation**: Chart generation meets performance requirements

- **Generation Time**: **365ms** (requirement: <3 seconds)
- **Chart Type**: Line chart (matplotlib)
- **Format**: PNG, 150 DPI
- **Backend**: Agg (non-interactive, server-safe)
- **Quality**: ✅ Readable and well-styled

**Performance Test**:
```
✓ Chart generated in 365ms
  Requirement: <3000ms
  Performance: 8x faster than requirement
```

### ✅ FastAPI + Async

**Validation**: All components integrate smoothly

- FastAPI async endpoints work with Pydantic-AI agent
- Garth library compatible with FastAPI async patterns
- No blocking operations or event loop issues
- CORS middleware configured for local testing

## Decision: **PROCEED** ✅

All success criteria met. Recommend proceeding to Phase 1.

**Rationale**:
1. **Pydantic-AI** produces coherent, actionable fitness insights ✅
2. **Garmin OAuth** + MFA works reliably (including token persistence) ✅
3. **Visualization generation** completes in <3s (365ms measured) ✅
4. **FastAPI async patterns** work smoothly with garth ✅

**Confidence Level**: **High**
**Risk Assessment**: **Low** - All major integrations validated

## Identified Risks for Phase 1

### Low Risk

- **Pydantic-AI Cost**: Use gpt-4o-mini ($0.002/1K tokens) - acceptable
- **garth Stability**: Library actively maintained, proven in garmin_agents
- **Matplotlib Performance**: Well under performance requirements

### Medium Risk (Mitigated)

- **MFA Handling**: Spike uses interactive prompt; Phase 1 will implement web flow with `GarminMFARequired` exception pattern (validated in garmin_agents)
- **Token Refresh**: garth handles automatically; Phase 1 will add retry logic

### No Risk Identified

- FastAPI + async compatibility ✅
- Visualization quality ✅
- Data fetching reliability ✅

## Scope Adjustments for Phase 1

**No major adjustments required**.

**Minor recommendations**:
1. Implement web-based MFA flow (use exception pattern from garmin_agents)
2. Add retry logic for transient Garmin API errors
3. Use gpt-4o-mini for cost optimization (already validated)

## Next Steps

1. **Review spike with stakeholders** (if applicable)
2. **Proceed to Phase 1**: Infrastructure Foundation
   - Complete project structure (all folders from day one)
   - Authentication service (JWT + bcrypt)
   - User registration/login endpoints
   - Frontend templates
   - Telemetry workspace package
   - 80%+ test coverage

3. **Cleanup spike artifacts** (optional):
   - Keep spike/ folder for reference during Phase 1
   - Delete after Phase 1 completion

## Files Structure

```
spike/
├── main.py                    # 99 lines - FastAPI app
├── chat_agent.py              # 176 lines - Pydantic-AI agent
├── garmin_client.py           # 194 lines - Garmin integration
├── viz_generator.py           # 64 lines - Chart generation
├── tests/
│   └── test_integration.py    # 72 lines - Integration tests
├── cache/                     # Runtime cache (not committed)
│   ├── garmin_tokens          # Saved tokens
│   ├── viz_*.png             # Generated charts
│   └── *.json                # Cached activities/metrics
├── pyproject.toml             # Dependencies
├── .env.example               # Environment template
├── README.md                  # This file
└── DECISION.md               # Detailed validation results
```

**Total Lines of Code**: ~605 lines (excluding tests, config, docs)

## Lessons Learned

1. **TestModel Limitations**: Pydantic-AI's TestModel provides minimal test data (e.g., 'a' for string args), which causes tool execution failures when tools expect specific formats (dates, etc.). Real API testing requires OPENAI_API_KEY.

2. **Garmin Token Persistence**: Garth's `.dump()`/`.load()` pattern works well for token management. Store per-user tokens in separate directories for multi-user scenarios.

3. **Matplotlib Backend**: Must use `matplotlib.use('Agg')` before importing pyplot for server compatibility (non-interactive backend).

4. **AsyncClient Testing**: FastAPI tests with httpx require `ASGITransport(app=app)` pattern, not `app=app` directly.

## References

- **Pydantic-AI Docs**: https://ai.pydantic.dev/
- **garth Library**: https://github.com/matin/garth
- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **Reference Projects**:
  - CliniCraft: `/Users/bryn/repos/clinicraft/` (infrastructure patterns)
  - Garmin Agents: `/Users/bryn/repos/garmin_agents/` (Garmin integration)

---

**Spike Duration**: 1 development session (~8 hours)
**Recommendation**: **PROCEED to Phase 1** ✅
