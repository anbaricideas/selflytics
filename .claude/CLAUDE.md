# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Context

**Selflytics** - AI-powered analysis for quantified self data from wearable devices (Garmin integration)

- **Status**: 🚧 Specification Phase Complete
- **GCP Project**: selflytics-infra (174666459313, australia-southeast1)
- **Tech Stack**: FastAPI + Pydantic-AI + Firestore + Jinja2/HTMX/Alpine.js + Terraform
- **Package Manager**: uv (not pip/poetry)

## Reference Projects (Proven Patterns to Reuse)

- **CliniCraft** (`/Users/bryn/repos/clinicraft/`) - Infrastructure, auth, Pydantic-AI, frontend, telemetry
- **Garmin Agents** (`/Users/bryn/repos/garmin_agents/`) - Garmin integration, token management, MFA flows

## High-Level Structure

```
backend/
├── app/
│   ├── auth/              # JWT, password hashing
│   ├── services/          # Business logic
│   ├── routes/            # API endpoints
│   ├── models/            # Pydantic models
│   ├── templates/         # Jinja2 templates
│   └── main.py
├── packages/telemetry/    # Workspace package (OpenTelemetry + Cloud Logging)
└── tests/                 # unit/, integration/, e2e/
infra/                     # Terraform modules + environments
docs/
├── SELFLYTICS_SPECIFICATION.md
├── project-setup/
│   ├── ROADMAP.md        # Overall status
│   └── PHASE_*_plan.md   # Detailed phase steps
```

## Key Documents to Reference

1. **Specification**: `docs/SELFLYTICS_SPECIFICATION.md` - Complete technical design
2. **Roadmap**: `docs/project-setup/ROADMAP.md` - Current phase, overall progress
3. **Phase Plans**: `docs/project-setup/PHASE_*_plan.md` - Step-by-step implementation guides
4. **Patterns Guide**: `docs/REUSABLE_PATTERNS_GUIDE.md` - Reusable patterns from Garmin Agents

## Common Commands

```bash
# Dependencies
uv sync --all-extras
uv add <package>

# Development
./scripts/dev-server.sh  # Loads backend/.env, uses PORT variable

# Local E2E Testing
./scripts/local-e2e-server.sh  # Start Firestore emulator + dev server
# Then in another terminal:
uv --directory backend run pytest tests/e2e_playwright -v --headed

# Testing (TDD required, 80%+ coverage)
uv --directory backend run pytest tests/ -v --cov=app
uv --directory backend run pytest tests/unit -v
uv --directory backend run pytest tests/integration -v
uv --directory backend run pytest -k "test_name" -v

# Code quality
uv run ruff check .
uv run ruff format .
uv run bandit -c backend/pyproject.toml -r backend/app/ -ll

# Infrastructure
terraform -chdir=infra/environments/dev plan
terraform -chdir=infra/environments/dev apply

# Hours estimate
git log --oneline main..HEAD --format="%ad" --date=format:"%Y-%m-%d %H:00" | uniq | wc -l
```

## Development Workflow

See **[docs/DEVELOPMENT_WORKFLOW.md](../docs/DEVELOPMENT_WORKFLOW.md)** for complete workflow guidelines including:
- TDD cycle and local testing practices
- E2E testing guidelines and local-first approach
- Manual testing recommendations
- Commit guidelines and quality gates

**Quick reference**:
1. **Follow Roadmap**: Check `ROADMAP.md` for ⏳ NEXT phase
2. **Read Phase Plan**: Detailed steps in `PHASE_*_plan.md`
3. **TDD Workflow**: Test first → verify fail → implement → verify pass → commit
4. **Local E2E Testing**: Use `./scripts/local-e2e-server.sh` for local e2e validation
5. **Track Progress**: Mark ✅ DONE in phase plan (single source of truth)
6. **Commit Often**: Clear conventional commit messages

## Planning and Time Tracking

**❌ DO NOT include time estimates** for future work in phase plans or roadmaps. Time estimates are unreliable and create false expectations.

**✅ DO track actual time** for completed work using git timestamps:
```bash
# Hours estimate for completed work (accurate)
git log --oneline main..HEAD --format="%ad" --date=format:"%Y-%m-%d %H:00" | uniq | wc -l
```

- Phase plans should describe **what** needs to be done, not **how long** it will take
- Roadmap tracks actual time for completed phases only
- Focus on deliverables and success criteria, not duration

## Critical Patterns

### Security - PII Redaction (ALWAYS)

```python
from app.utils.redact import redact_for_logging

# ✅ CORRECT
logger.error("API error: %s", redact_for_logging(str(e)))
logger.info("User %s authenticated", redact_for_logging(username))

# ❌ WRONG - f-strings bypass redaction, leak PII
logger.error(f"Error: {error}")
```

**Enforced by pre-commit hook** - never use f-strings in logger calls.

### Async/Await (FastAPI is async)

```python
@router.post("/endpoint")
async def my_endpoint(data: MyModel):
    result = await my_service.process(data)  # Always await
    return result
```

### Authentication (JWT)

```python
from app.auth.dependencies import get_current_user

@router.get("/protected", dependencies=[Depends(get_current_user)])
async def protected_route():
    # Only accessible with valid JWT
```

### Pydantic Models (Validation)

```python
class User(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    email: EmailStr
    password: str = Field(..., min_length=8)
```

## Important Conventions

- **Imports**: Always at top of file (never inside functions)
- **Type hints**: Modern syntax (`list[str]` not `List[str]`)
- **Spelling**: Prefer "analyse" over "analyze"
- **Async**: Use async/await consistently
- **Branch naming**: `feat/phase-N-description`
- **Commit format**: Conventional commits (`feat:`, `fix:`, `test:`, `docs:`, `chore:`)

## Common Pitfalls

1. ❌ **Don't use `cd` in Bash commands** - use absolute paths instead
2. ❌ **Don't use f-strings in logs** - use % formatting for redaction
3. ❌ **Don't skip TDD** - write tests first, 80%+ coverage required
4. ❌ **Don't commit secrets** - use Secret Manager
5. ❌ **Don't bypass async** - FastAPI requires async/await
6. ❌ **Don't create new docs** - update existing instead
7. ❌ **Don't push after every commit** - only when needed (e.g., CI)
8. ❌ **Don't progress with failing tests** - fix ALL before PR

## Testing Requirements

- **80%+ coverage required** (enforced by CI)
- **TDD workflow mandatory**: Test → Fail → Implement → Pass → Commit
- **Test pyramid**: 60% unit, 30% integration, 10% e2e
- Mock external services (Firestore, Garmin API, OpenAI)

### E2E Testing Workflow

When fixing e2e test failures, **use agents first, manual debugging second**:

#### Decision Tree for Test Failures

**Use @agent-debug-investigator IMMEDIATELY when:**
- ≥3 tests failing with similar error pattern
- Test failures have unclear root cause
- Multiple theories exist but uncertain which is correct
- Behavior works manually but fails in tests
- Timeout errors without obvious cause

**Use direct tools when:**
- Single specific file lookup needed
- You know the exact solution already
- Linear task with clear, simple steps
- Quick verification of known facts

#### E2E Debugging Process

1. **DIAGNOSE FIRST** - Use @agent-debug-investigator before attempting fixes
   ```
   Prompt: "N tests failing with [error pattern]. Pattern: [description].
   Run in headed mode to diagnose root cause with evidence."
   ```

2. **UNDERSTAND ROOT CAUSE** - Don't guess, get systematic evidence:
   - Headed mode observation (what actually happens in browser)
   - Browser console logs (JavaScript errors)
   - Network tab inspection (request/response details)
   - Screenshot comparison (expected vs actual)

3. **FIX SYSTEMATICALLY** - Address root cause, not symptoms:
   - Fix the underlying issue, not just failing assertions
   - Validate fix addresses root cause, not masking problem
   - Consider if fix applies to similar patterns elsewhere

4. **VERIFY THOROUGHLY** - Run ALL tests after fixes:
   ```bash
   uv --directory backend run pytest tests/e2e_playwright -v
   ```

#### Common Playwright/HTMX Patterns

Reference these before debugging (may save investigation time):

✅ **Playwright route interception**: Captures ALL HTTP methods
- Must explicitly handle each method type
- GET requests need `route.continue_()` to pass through
- Pattern: `if route.request.method == "GET": route.continue_(); return`

✅ **HTMX error swapping**: Doesn't swap 4xx/5xx by default
- Requires `htmx:beforeSwap` event listener configuration
- Pattern: `if (evt.detail.xhr.status === 400) { evt.detail.shouldSwap = true; }`
- Place script at end of `<body>` or use DOMContentLoaded

✅ **Browser authentication**: Needs redirect handlers, not JSON errors
- FastAPI exception handlers for 401/403
- Check Accept header to distinguish browser vs API requests
- Use 303 redirects for browser requests to `/login`

✅ **JavaScript timing**: Event listeners need DOM ready
- Scripts in `<head>` run before DOM exists
- Place interactive scripts at end of `<body>` or wrap in DOMContentLoaded
- HTMX/Alpine.js event listeners especially sensitive to timing

## Environment Setup

Copy `.env.example` files and populate:
- **Root**: GCP project details
- **Backend**: JWT secrets, API keys (from Secret Manager)

Secrets NEVER committed - stored in GCP Secret Manager.
