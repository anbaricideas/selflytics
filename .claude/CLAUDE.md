# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Context

**Selflytics** - AI-powered analysis for quantified self data from wearable devices (Garmin integration)

- **GCP Project**: selflytics-infra (174666459313, australia-southeast1)
- **Tech Stack**: FastAPI + Pydantic-AI + Firestore + Jinja2/HTMX/Alpine.js + Terraform
- **Package Manager**: uv (not pip/poetry)

## Reference Projects (Proven Patterns to Reuse)

- **CliniCraft** (`/Users/bryn/repos/clinicraft/`) - Infrastructure, auth, Pydantic-AI, frontend, telemetry
- **Garmin Agents** (`/Users/bryn/repos/garmin_agents/`) - Garmin integration, token management, MFA flows

## Key Documents to Reference

1. **Specification**: `docs/SELFLYTICS_SPECIFICATION.md` - Complete technical design
2. **Roadmap**: `docs/project-setup/ROADMAP.md` - Current phase, overall progress
3. **Phase Plans**: `docs/project-setup/PHASE_*_plan.md` - Step-by-step implementation guides
4. **Development Workflow**: `docs/DEVELOPMENT_WORKFLOW.md` - TDD cycle, testing practices, commit guidelines
5. **Patterns Guide**: `docs/REUSABLE_PATTERNS_GUIDE.md` - Reusable patterns from Garmin Agents

## Project Structure

```
backend/
├── app/                   # Main application code
├── packages/telemetry/    # Workspace package (OpenTelemetry + Cloud Logging)
└── tests/                 # unit/, integration/, e2e_playwright/
infra/                     # Terraform modules + environments
docs/                      # Specification, roadmap, phase plans, guides
```

## Common Commands

```bash
# Dependencies
uv sync --all-extras
uv add <package>

# Development
./scripts/dev-server.sh  # Loads backend/.env, uses PORT variable

# Local E2E Testing (requires both emulator + server)
./scripts/local-e2e-server.sh  # Start Firestore emulator + dev server
# Then in another terminal:
uv --directory backend run pytest tests/e2e_playwright -v --headed

# Testing (TDD required, 80%+ coverage)
uv --directory backend run pytest tests/ -v --cov=app
uv --directory backend run pytest tests/unit -v
uv --directory backend run pytest tests/integration -v

# Code quality
uv run ruff check .
uv run ruff format .
uv run bandit -c backend/pyproject.toml -r backend/app/ -ll

# Infrastructure
terraform -chdir=infra/environments/dev plan
terraform -chdir=infra/environments/dev apply

# Actual hours spent (completed work only)
git log --oneline main..HEAD --format="%ad" --date=format:"%Y-%m-%d %H:00" | uniq | wc -l
```

## Development Workflow

### Phase Implementation Workflow

1. **Check ROADMAP.md** for current phase (marked ⏳ NEXT or IN PROGRESS)
2. **Read phase plan** (`PHASE_*_plan.md`) - this is the single source of truth
3. **Follow TDD**: Test first → verify fail → implement → verify pass → commit
4. **Track progress**: Update checkboxes in phase plan as you complete steps
5. **Commit often**: Clear conventional commit messages after each major step

### CRITICAL: Blocked Step Protocol

**When you encounter ANY step you cannot complete autonomously:**

1. **STOP immediately** - do not proceed to the next step
2. **Use AskUserQuestion tool** with explicit options:
   - Execute this step now (with my help)
   - Defer this step (document reason and come back later)
   - Skip permanently (mark as WON'T DO with approval)
   - Other approach (user specifies)
3. **Wait for explicit user choice** - NEVER assume or infer intent
4. **Document the decision** in the phase plan before proceeding

**Pre-flight check before moving to next step:**
- ✅ Did I complete this step fully?
- ❌ If NO: Did I get explicit user approval to skip/defer?
- 🛑 If NO approval: STOP and use AskUserQuestion

**Example scenarios requiring AskUserQuestion:**
- Step requires user to execute manual testing
- Step requires external tool/access I don't have
- Step requires user decision between multiple approaches
- Step unclear or contradicts other information
- Any situation where I'm tempted to "skip for now"

### Phase Completion Verification

**BEFORE claiming a phase complete**, verify ALL of the following:

1. ✅ **Every step checkbox** in phase plan is checked (not just session summaries)
2. ✅ **Every deliverable file exists** on filesystem (verify with `find`/`ls`/`grep`)
3. ✅ **All success criteria** checkboxes are checked
4. ✅ **All validation checks pass** (tests, coverage ≥80%, lint, security scan)

**If any verification fails**:
- Mark step status honestly: ❌ NOT DONE, ⚠️ PARTIAL, ✅ DONE
- ASK user: "Steps X-Y incomplete. Should I: (A) complete them, (B) defer them, (C) other?"
- Document user's decision in plan
- NEVER defer scope without explicit user approval

**If you see contradictory information** (e.g., session summary says complete but checkboxes unchecked):
- Checkboxes are source of truth
- Ask user to clarify if uncertain

### Handling Conflicting Information

When phase plan sections conflict:
- **Step-by-step checkboxes** = authoritative source of truth
- **Session summaries** = informal notes only
- If in doubt, ask rather than assume

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
9. ❌ **Don't claim phase complete without verifying all checkboxes**
10. ❌ **Don't defer scope without explicit user approval**

## Testing Requirements

- **80%+ coverage required** (enforced by CI)
- **TDD workflow mandatory**: Test → Fail → Implement → Pass → Commit
- **Test pyramid**: 60% unit, 30% integration, 10% e2e
- Mock external services (Firestore, Garmin API, OpenAI)

### E2E Testing Workflow

**Running E2E tests requires infrastructure**:
- Firestore emulator must be running
- Dev server must be running at configured PORT
- Use `./scripts/local-e2e-server.sh` to start both

**When fixing e2e test failures**:

Use **@agent-debug-investigator** when:
- ≥3 tests failing with similar error pattern
- Test failures have unclear root cause
- Multiple theories exist but uncertain which is correct
- Behavior works manually but fails in tests
- Timeout errors without obvious cause

Use **direct tools** when:
- Single specific file lookup needed
- You know the exact solution already
- Linear task with clear, simple steps

**E2E Debugging Process**:
1. **DIAGNOSE FIRST** - Use @agent-debug-investigator before attempting fixes
2. **UNDERSTAND ROOT CAUSE** - Get systematic evidence (headed mode, console logs, network tab)
3. **FIX SYSTEMATICALLY** - Address root cause, not symptoms
4. **VERIFY THOROUGHLY** - Run ALL tests after fixes

**Common Playwright/HTMX Patterns**:
- **Route interception**: Must explicitly handle GET requests (`route.continue_()`)
- **HTMX error swapping**: Requires `htmx:beforeSwap` event listener for 4xx/5xx
- **Browser authentication**: Needs 401 redirect handlers (check Accept header)
- **JavaScript timing**: Event listeners need DOM ready (place scripts at end of `<body>`)

## Environment Setup

Copy `.env.example` files and populate:
- **Root**: GCP project details
- **Backend**: JWT secrets, API keys (from Secret Manager)

Secrets NEVER committed - stored in GCP Secret Manager.
