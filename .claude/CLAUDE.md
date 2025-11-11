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
uv run --directory backend uvicorn app.main:app --reload

# Testing (TDD required, 80%+ coverage)
uv run pytest backend/tests/ -v --cov=app
uv run pytest backend/tests/unit -v
uv run pytest -k "test_name" -v

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

1. **Follow Roadmap**: Check `ROADMAP.md` for ⏳ NEXT phase
2. **Read Phase Plan**: Detailed steps in `PHASE_*_plan.md`
3. **TDD Workflow**: Test first → verify fail → implement → verify pass → commit
4. **Track Progress**: Mark ✅ DONE in phase plan (single source of truth)
5. **Commit Often**: Clear conventional commit messages

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

## Environment Setup

Copy `.env.example` files and populate:
- **Root**: GCP project details
- **Backend**: JWT secrets, API keys (from Secret Manager)

Secrets NEVER committed - stored in GCP Secret Manager.
