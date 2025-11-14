# Selflytics Implementation Roadmap

**Project**: Selflytics - AI-powered analysis for quantified self data
**Started**: 2025-11-11
**Status**: Ready for Implementation
**Based on**: `/Users/bryn/repos/selflytics/docs/SELFLYTICS_SPECIFICATION.md`
**GitHub Repo**: https://github.com/anbaricideas/selflytics
**GCP Project**: selflytics-infra (174666459313)

---

## Executive Summary

Selflytics is a multi-user SaaS application providing AI-powered analysis and insights for quantified self data from wearable devices. The initial version focuses on Garmin ecosystem integration with natural language chat interface augmented by AI-generated visualizations.

**Core Value Proposition**:
- Natural language interface for exploring personal fitness data
- AI-driven trend forecasting and personalized insights
- Visual analysis generated on-demand in response to user queries
- Secure, privacy-focused personal health data management

**Technology Foundation**:
- Reuses proven infrastructure from CliniCraft (Pydantic-AI, FastAPI, Cloud Run, Terraform, Cloud Logging telemetry)
- Reuses Garmin integration patterns from Garmin Agents (garth library, token management)
- Modern progressive-enhancement frontend (Jinja2 + HTMX + Alpine.js + TailwindCSS)
- Well-structured monorepo from day one (follows CliniCraft folder organization)

**Key Project Details**:
- **GCP Project ID**: selflytics-infra
- **Region**: australia-southeast1 (Sydney)
- **Production Domain**: selflytics.anbaricideas.com
- **Reference Projects**:
  - CliniCraft at `/Users/bryn/repos/clinicraft/` (infrastructure patterns)
  - Garmin Agents at `/Users/bryn/repos/garmin_agents/` (Garmin integration patterns)

---

## Implementation Strategy

### Core Principles

1. **Spike-Then-Phase Approach**: Validate core technical assumptions before committing to full implementation
2. **TDD Workflow**: Write tests first, review with quality gates, then implement
3. **Proven Patterns**: Reuse CliniCraft infrastructure and Garmin Agents integration code
4. **Privacy-First**: Secure token storage, PII redaction, minimal data retention
5. **Progressive Enhancement**: Server-first rendering with layered client enhancements

### Development Approach

**Phase Progression**:
```
Spike (1 week)
  ↓ Decision Point: Proceed if core assumptions validated
Phase 1: Infrastructure Foundation (2 weeks)
  ↓
Phase 2: Garmin Integration (2 weeks)
  ↓
Phase 3: Chat Interface + AI Agent (3 weeks)
  ↓
Phase 4: E2E Test Fixes & User Journey Verification (1 week)
  ↓
Phase 5: Visualization Generation (2 weeks) [Future]
  ↓
Phase 6: Goals & Polish (1 week) [Future]
  ↓
Phase 7: Launch Preparation (1 week) [Future]
```

**This Roadmap Covers**: Spike + Phases 1-4 (detailed plans provided)
**Future Phases**: Phases 5-7 will be planned after Phase 4 completion

### Git Workflow

```
main
  ← feat/selflytics-spike (PR after spike validation)
  ← feat/phase-1-infrastructure (PR after Phase 1 complete)
  ← feat/phase-2-garmin (PR after Phase 2 complete)
  ← feat/phase-3-chat-ai (PR after Phase 3 complete)
  ← feat/phase-4-e2e-fixes (PR after Phase 4 complete)
```

**Branch Protection**:
- All PRs require CI passing (lint, test, security, terraform validation)
- No direct pushes to main
- Preview deployments for all feature branches

### Session Startup Command

When ready to implement each phase:

```
I'm continuing the first incomplete phase of work from the roadmap described in @docs/project-setup/ROADMAP.md
The roadmap points to a planning document for that phase. You should use that.

Guidelines:
1. Follow the relevant phase planning document as the single source of truth
2. Use TDD: write tests first, review with test quality checks, then implement
3. Commit after each major step with clear commit messages
4. Follow CLAUDE.md guidelines (imports at top, uv for dependencies, etc.)
5. All progress tracking in the planning document only - no separate docs
6. Ask questions only if blocked or contradictory info found

Start from: wherever marked as ⏳ NEXT
```

---

## Phase Overview

| Phase | Description | Status | Actual Time | Branch | PR |
|-------|-------------|--------|-------------|--------|-----|
| [Spike](./SPIKE_plan.md) | Technical Validation | ✅ DONE | 8 hours | `feat/selflytics-spike` | - |
| [1](./PHASE_1_plan.md) | Infrastructure Foundation | ✅ DONE | 7 hours | `feat/phase-1-infrastructure` | - |
| [2](./PHASE_2_plan.md) | Garmin Integration | ✅ DONE | 5 hours | `feat/phase-2-garmin` | - |
| [3](./PHASE_3_plan.md) | Chat + AI Agent | ✅ DONE | 6 hours | `feat/phase-3-chat-ai` | - |
| [4](./PHASE_4_plan.md) | E2E Test Fixes & User Journeys | ⏳ IN PROGRESS | ~7 hours so far | `feat/phase-4-e2e-fixes` | - |
| 5 | Visualization Generation | 📅 PLANNED | - | TBD | - |
| 6 | Goals & Polish | 📅 PLANNED | - | TBD | - |
| 7 | Launch Preparation | 📅 PLANNED | - | TBD | - |

**Current Phase**: ⏳ Phase 4 In Progress → [Phase 4 Plan](./PHASE_4_plan.md) (integration tests fixed, all 303 tests passing)

---

## Dependencies

### Required Tools (Install Before Starting)
- ✅ uv (package manager) - `curl -LsSf https://astral.sh/uv/install.sh | sh`
- ✅ Python 3.12+
- ✅ Terraform 1.5+
- ✅ gcloud CLI - configured for GCP project `selflytics-infra`
- ✅ Git

### Required GCP Resources (Already Configured)
- ✅ GCP project: selflytics-infra (174666459313)
- ✅ Billing enabled
- ✅ GitHub repository: https://github.com/anbaricideas/selflytics

### New Dependencies to Add During Implementation
- `pydantic-ai` - AI agent framework (Phase 3)
- `garth` - Garmin Connect integration (Phase 2)
- `matplotlib` + `Pillow` - Visualization generation (Phase 5)
- `fastapi` + `uvicorn` - Web framework (Phase 1)
- `google-cloud-firestore` - Database (Phase 1)
- `google-cloud-secret-manager` - Secrets (Phase 1)
- `python-jose[cryptography]` - JWT tokens (Phase 1)
- `passlib[bcrypt]` - Password hashing (Phase 1)
- `playwright` - E2E testing (Phase 4)

### Environment Variables (To Configure)

**Project Root `.env` (Infrastructure)**:
```bash
GCP_PROJECT_ID=selflytics-infra
GCP_REGION=australia-southeast1
WIF_PROVIDER=projects/174666459313/locations/global/workloadIdentityPools/github-pool/providers/github-provider
WIF_SERVICE_ACCOUNT=github-actions@selflytics-infra.iam.gserviceaccount.com
```

**Backend `.env` (Application)**:
```bash
# Application
ENVIRONMENT=dev
DEBUG=true

# Database
FIRESTORE_DATABASE=(default)

# Authentication
JWT_SECRET_KEY=<from Secret Manager>
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# AI Services
OPENAI_API_KEY=<from Secret Manager>
OPENAI_MODEL=gpt-4.1-mini-2025-04-14

# Garmin OAuth
GARMIN_CLIENT_ID=<from Garmin Developer Portal>
GARMIN_CLIENT_SECRET=<from Secret Manager>

# Telemetry
TELEMETRY_BACKEND=cloudlogging
```

---

## Testing Strategy

### Test Pyramid

```
        ┌───────────┐
        │    E2E    │  10% - Full user workflows
        │   Tests   │
        └───────────┘
      ┌───────────────┐
      │  Integration  │  30% - API endpoints, DB interactions
      │     Tests     │
      └───────────────┘
    ┌───────────────────┐
    │   Unit Tests      │  60% - Services, models, utilities
    │                   │
    └───────────────────┘
```

### TDD Workflow (Every Phase)

1. **Write Test First**: Define expected behavior with test cases
2. **Review Tests**: Check test quality and coverage
3. **Verify Failure**: Run tests, confirm they fail (no implementation yet)
4. **Implement**: Write minimal code to pass tests
5. **Verify Success**: Run tests, confirm they pass
6. **Refactor**: Clean up code while keeping tests green
7. **Commit**: Save progress with clear commit message

### Test Organization

```
backend/tests/
├── unit/               # Fast, isolated unit tests
│   ├── services/       # Business logic
│   ├── models/         # Pydantic models
│   └── utils/          # Utilities
├── integration/        # API endpoint tests
│   ├── routers/        # Route handlers
│   └── test_*.py       # DB interactions
└── e2e_playwright/     # End-to-end workflows
    └── test_*.py       # Complete user journeys
```

### Coverage Requirements

- **Minimum**: 80% coverage on all new code
- **Enforcement**: CI fails if coverage drops below threshold
- **Reporting**: Coverage reports generated on each PR

### Test Patterns from Reference Projects

**From CliniCraft**:
- Pytest fixtures for test users, mocked Firestore
- FastAPI TestClient for API testing
- Mocked external services (OpenAI API)
- Async test patterns with pytest-asyncio

**From Garmin Agents**:
- Mocked Garmin API responses
- Token management test scenarios
- MFA flow testing patterns
- Exception handling tests

---

## Quality Gates

### Per-Phase Quality Checks

Before marking a phase complete:

1. **Code Quality**:
   - [ ] `uv run ruff check .` passes with no errors
   - [ ] `uv run ruff format --check .` passes
   - [ ] All pre-commit hooks passing

2. **Testing**:
   - [ ] All new tests passing
   - [ ] 80%+ coverage on new code
   - [ ] Integration tests demonstrate workflow (if applicable)

3. **Documentation**:
   - [ ] Phase plan updated with completion status
   - [ ] All implementation steps marked ✅ DONE
   - [ ] Commit messages follow conventional commits format

4. **Manual Validation** (Phase-specific):
   - See individual phase plans for specific checks

---

## Common Commands

### Development

```bash
# Install dependencies (run after adding new packages)
uv sync --all-extras

# Run local development server
uv run --directory backend uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# Run all CI checks locally
uv run ruff check .
uv run ruff format --check .
uv run pytest backend/tests/unit -v --cov=app
uv run bandit -c backend/pyproject.toml -r backend/app/ -ll

# Format code
uv run ruff format .
uv run ruff check --fix .

# Run tests by category
uv run pytest backend/tests/unit -v                    # Unit tests only
uv run pytest backend/tests/integration -v             # Integration tests
uv run pytest backend/tests/e2e_playwright -v          # E2E tests

# Check coverage
uv run pytest --cov=app --cov-report=term-missing --cov-report=html
```

### Infrastructure

```bash
# Initialize Terraform (first time only)
terraform -chdir=infra/environments/dev init

# Plan infrastructure changes
terraform -chdir=infra/environments/dev plan

# Apply infrastructure changes (requires confirmation)
terraform -chdir=infra/environments/dev apply

# Validate Terraform configuration
terraform -chdir=infra/environments/dev validate

# Check deployment readiness
./scripts/check-readiness.sh

# Validate deployed environment
./scripts/validate-deployment.sh http://localhost:8000
```

### Git Workflow

```bash
# Create feature branch
git checkout -b feat/selflytics-spike main

# Stage and commit changes
git add .
git commit -m "feat: implement core validation"

# Push to remote
git push -u origin feat/selflytics-spike

# Create PR (via GitHub UI or gh CLI)
gh pr create --base main --title "Spike: Technical Validation"

# Hours estimate for branch
git log --oneline main..HEAD --format="%ad" --date=format:"%Y-%m-%d %H:00" | uniq | wc -l
```

---

## Success Criteria

### Spike Success Criteria

Decision point: Proceed to Phase 1 if ALL criteria met

**Technical Validation**:
- [ ] Pydantic-AI agent produces coherent, actionable fitness insights
- [ ] Garmin OAuth + data fetch works reliably (including MFA)
- [ ] Visualization generation completes in <3 seconds
- [ ] FastAPI async patterns work with garth library

**Deliverables**:
- [ ] Minimal chat agent with 2-3 tools (get_activities, get_metrics)
- [ ] Garmin authentication flow (MFA supported)
- [ ] 1 week of activities fetched and cached locally
- [ ] 1 chart type (line chart) generated from mock data

### Phase 1 Success Criteria (Infrastructure Foundation)

**Technical Success**:
- [ ] User can register, login, access dashboard
- [ ] CI passes all quality gates (lint, test, security)
- [ ] Infrastructure deployed to dev environment
- [ ] Terraform applies successfully
- [ ] Cloud Logging telemetry working

**Deliverables**:
- [ ] Complete project structure (all folders from day one)
- [ ] Authentication service (JWT + bcrypt)
- [ ] User registration/login endpoints
- [ ] Frontend templates (base.html, login.html, register.html, dashboard.html)
- [ ] Telemetry workspace package
- [ ] 80%+ test coverage for auth flows

### Phase 2 Success Criteria (Garmin Integration)

**Technical Success**:
- [ ] User can link Garmin account via OAuth
- [ ] Activities from last 30 days cached in Firestore
- [ ] Cache invalidation works (24-hour TTL)
- [ ] MFA flow completes successfully (tested manually)
- [ ] Token encryption with KMS working

**Deliverables**:
- [ ] Garmin OAuth flow (link account from settings)
- [ ] GarminClient service (async wrapper around garth)
- [ ] Token storage in Firestore (encrypted)
- [ ] Data caching layer with TTL
- [ ] Pydantic models for Garmin data
- [ ] 80%+ test coverage (mocked Garmin API)

### Phase 3 Success Criteria (Chat + AI)

**Technical Success**:
- [ ] User can ask "How am I doing?" and get relevant insights
- [ ] Agent cites specific activities/dates in responses
- [ ] Conversation history persists across sessions
- [ ] Token usage tracked, costs under $0.05 per conversation
- [ ] Cost tracking integrated

**Deliverables**:
- [ ] Pydantic-AI chat agent with tools
- [ ] System prompts for fitness insights
- [ ] Conversation management (Firestore)
- [ ] Chat UI (Jinja2 + HTMX)
- [ ] Message history context
- [ ] 80%+ test coverage (mocked OpenAI)

### Phase 4 Success Criteria (E2E Tests & User Journeys)

**Technical Success**:
- [ ] All 16 Playwright e2e tests passing locally
- [ ] E2E tests can be run by any developer (README instructions work)
- [ ] Test failures provide clear error messages and screenshots
- [ ] All templates have required `data-testid` attributes

**User Journey Success**:
- [ ] Manual runsheet completed (all journeys verified working)
- [ ] User can register → login → link Garmin → sync → chat
- [ ] Error handling graceful (clear messages, can retry)
- [ ] Accessibility verified (keyboard nav, screen reader compatible)

**Documentation**:
- [ ] E2E testing guide clear and actionable
- [ ] Troubleshooting guide covers common issues
- [ ] Manual runsheet can be used by non-developers

---

## Timeline Estimate

| Phase | Duration | Effort (hours) | Cumulative |
|-------|----------|----------------|------------|
| **Spike** | 1 week | 40 | 40 |
| **Phase 1** | 2 weeks | 80 | 120 |
| **Phase 2** | 2 weeks | 80 | 200 |
| **Phase 3** | 3 weeks | 120 | 320 |
| **Phase 4** | 1 week | 40 | 360 |
| **Phase 5** | 2 weeks | 80 | 440 |
| **Phase 6** | 1 week | 40 | 480 |
| **Phase 7** | 1 week | 40 | 520 |
| **TOTAL** | **13 weeks** | **520 hours** | - |

**This Roadmap Scope**: Spike + Phases 1-4 (360 hours, 9 weeks)

**Assumptions**:
- 40 hours/week (full-time)
- 20% buffer included for debugging, refactoring
- No major scope changes during development

---

## Risk Mitigation

### Technical Risks

**Risk**: Garmin API rate limits or connectivity issues
- **Mitigation**: Implement caching with generous TTLs
- **Mitigation**: Retry logic with exponential backoff
- **Mitigation**: Store raw API responses for debugging

**Risk**: Pydantic-AI migration from smolagents more complex than expected
- **Mitigation**: Spike validates migration pattern first
- **Mitigation**: Reference CliniCraft blog generator patterns
- **Mitigation**: Start with 2-3 simple tools, expand later

**Risk**: OpenAI API costs higher than expected
- **Mitigation**: Use gpt-4.1-mini (cost-effective)
- **Mitigation**: Track token usage meticulously
- **Mitigation**: Implement conversation length limits
- **Mitigation**: Cache AI responses where appropriate

**Risk**: MFA flow blocks automated testing
- **Mitigation**: Mock Garmin API in tests
- **Mitigation**: Manual testing for MFA scenarios
- **Mitigation**: Store test tokens for development

**Risk**: E2E tests brittle and flaky
- **Mitigation**: Phase 4 establishes robust test infrastructure
- **Mitigation**: Journey-driven tests focus on value, not implementation details
- **Mitigation**: Clear debugging guides and screenshots on failure

### Process Risks

**Risk**: Reference projects have incompatible patterns
- **Mitigation**: Spike validates all major integrations
- **Mitigation**: Copy-adapt incrementally, not wholesale
- **Mitigation**: Test each integration independently

**Risk**: Infrastructure deployment fails
- **Mitigation**: Reuse proven CliniCraft Terraform modules
- **Mitigation**: Deploy to dev environment first
- **Mitigation**: Preview deployments for testing

---

## History

| Date | Event | Notes |
|------|-------|-------|
| 2025-11-11 | Roadmap created | Spike + Phases 1-3 detailed plans |
| 2025-11-11 | Specification finalized | Based on SELFLYTICS_SPECIFICATION.md v1.0 |
| 2025-11-11 | GCP project created | selflytics-infra (174666459313) |
| 2025-11-11 | GitHub repo created | https://github.com/anbaricideas/selflytics |
| 2025-11-11 | Spike completed ✅ | 8 hours (vs 40 est). Decision: PROCEED to Phase 1. All validation criteria met. |
| 2025-11-12 | Phase 1 completed ✅ | Infrastructure deployed, 87 tests (96% coverage), Cloud Run live (~7 hours) |
| 2025-11-13 | Phase 2 completed ✅ | Garmin integration complete, 179 tests (91% coverage), HTMX auth flow fixed (~5 hours) |
| 2025-11-13 | Phase 3 completed ✅ | Chat + AI agent complete, 187 tests (91-100% on Phase 3 code), Pydantic-AI with 3 Garmin tools (~6 hours) |
| 2025-11-14 | Phase 4 in progress | Core e2e fixes complete (16/16 tests pass), but documentation/validation steps incomplete (~4 hours so far) |

---

## References

**Project Documentation**:
- [Specification](../SELFLYTICS_SPECIFICATION.md) - Complete project specification
- [CLAUDE.md](../../.claude/CLAUDE.md) - Development workflow and conventions

**Reference Projects**:
- CliniCraft: `/Users/bryn/repos/clinicraft/`
  - Infrastructure patterns (Terraform, Cloud Run, Firestore)
  - Pydantic-AI integration (blog generator service)
  - Telemetry workspace package
  - Frontend patterns (Jinja2 + HTMX + Alpine.js)
- Garmin Agents: `/Users/bryn/repos/garmin_agents/`
  - GarminClient implementation
  - Token management patterns
  - MFA flow handling

**External Documentation**:
- [Pydantic-AI Documentation](https://ai.pydantic.dev/)
- [garth Library](https://github.com/matin/garth)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Firestore Documentation](https://cloud.google.com/firestore/docs)
- [Playwright Documentation](https://playwright.dev/)

---

*Last Updated: 2025-11-14*
*Status: Ready for Implementation*
