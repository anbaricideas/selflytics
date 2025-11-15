# CSRF Protection Improvements Implementation Roadmap

**Feature**: Close CSRF protection gaps for logout and chat endpoints
**GitHub Issue**: [#12 - Integrate CSRF protection into settings page logout form](https://github.com/anbaricidias/selflytics/issues/12)
**Specification**: `/Users/bryn/repos/selflytics/docs/development/csrf-improvements/SPECIFICATION.md`
**Parent Specification**: `/Users/bryn/repos/selflytics/docs/development/csrf/CSRF_SPECIFICATION.md`
**Status**: Not Started
**Created**: 2025-11-16
**Branch**: `chore/csrf-improvements` (main feature branch)

---

## Executive Summary

This roadmap closes two critical CSRF protection gaps identified during security review:
1. **Logout endpoint** (`POST /logout`) - vulnerable to forced logout attacks
2. **Chat send endpoint** (`POST /chat/send`) - vulnerable to message injection and resource consumption attacks

**Security Context**:
- **Base Protection**: PR #21 implemented comprehensive CSRF protection for auth and Garmin endpoints
- **Identified Gaps**: Security review found 2 unprotected endpoints (logout, chat/send)
- **Risk Level**: Medium (logout) to Medium-High (chat/send)
- **Impact**: DoS via forced logout, chat history pollution, API cost abuse, potential info leakage

**Implementation Approach**:
- **TDD workflow**: Write tests first, verify failure, implement, verify pass (strict test-first)
- **Quick phases**: 1-2 hour focused phases for rapid iteration
- **Standard E2E coverage**: Critical security scenarios (attack prevention, token handling)
- **Pattern reuse**: Follow existing CSRF patterns from PR #21 for consistency

---

## Implementation Strategy

### Core Principles

1. **Security First**: Close identified gaps to prevent real-world attacks
2. **Strict TDD**: Write tests before implementation in every step
3. **Pattern Consistency**: Reuse existing CSRF patterns (form-based and header-based)
4. **User Experience**: Graceful error handling with clear messages
5. **Minimal Changes**: Leverage existing infrastructure from PR #21

### Git Workflow

```
main
  ↓
chore/csrf-improvements (main feature branch - already exists)
  ↓
chore/csrf-improvements-phase-1 (PR into chore/csrf-improvements)
  ↓
chore/csrf-improvements-phase-2 (PR into chore/csrf-improvements)
  ↓
chore/csrf-improvements-phase-3 (PR into chore/csrf-improvements)
  ↓
chore/csrf-improvements → main (final PR)
```

**Branch Strategy**:
- Main feature branch `chore/csrf-improvements` already exists (current branch)
- Each phase implemented in a sub-branch (e.g., `chore/csrf-improvements-phase-1`)
- Sub-branches merge into `chore/csrf-improvements` via PR
- Final `chore/csrf-improvements` merges into `main` after all phases complete

### Session Startup Command

When ready to implement each phase:

```
I'm continuing work on CSRF improvements from the roadmap at @docs/development/csrf-improvements/ROADMAP.md

Guidelines:
1. Follow the phase planning document as single source of truth
2. Use STRICT TDD: write tests FIRST, verify they FAIL, implement, verify they PASS
3. Commit after each major step with clear commit messages
4. Follow CLAUDE.md guidelines (imports at top, uv for dependencies, PII redaction)
5. Track progress in phase plan checkboxes only
6. Ask questions if blocked or contradictory info found

Start from: wherever marked as ⏳ NEXT
```

### Quality Gates

Each phase must pass:
- ✅ All new tests pass (unit, integration, E2E where applicable)
- ✅ All existing tests still pass (no regressions)
- ✅ Test coverage ≥ 80% maintained
- ✅ Type checking passes: `uv run mypy backend/app`
- ✅ Linting passes: `uv run ruff check .`
- ✅ Security scan passes: `uv run bandit -c backend/pyproject.toml -r backend/app/ -ll`
- ✅ Manual testing checklist completed

---

## Phase Overview

| Phase | Description | Status | Branch | Estimated | Actual |
|-------|-------------|--------|--------|-----------|--------|
| [1](./PHASE_1_plan.md) | Protect Logout Endpoint | ⏳ NEXT | `chore/csrf-improvements-phase-1` | 1.5h | - |
| [2](./PHASE_2_plan.md) | Protect Chat Send Endpoint | NOT STARTED | `chore/csrf-improvements-phase-2` | 1.5h | - |
| [3](./PHASE_3_plan.md) | Documentation & Validation | NOT STARTED | `chore/csrf-improvements-phase-3` | 0.5h | - |

**Current Phase**: Phase 1 - Protect Logout Endpoint

**Total Estimated Time**: 3.5 hours across 3 phases

---

## Dependencies

### Required Packages (Already Installed)

```bash
# CSRF protection library (already installed in PR #21)
# fastapi-csrf-protect==0.3.4

# Testing dependencies (already installed)
# pytest, pytest-cov, pytest-asyncio
# beautifulsoup4 (for HTML parsing in tests)
# playwright (for E2E tests)
```

**No new dependencies required** - all infrastructure from PR #21 is already in place.

### Environment Variables (Already Configured)

```bash
# CSRF secret key (already in backend/.env from PR #21)
CSRF_SECRET="<your-secret-key-min-32-chars>"
```

---

## Testing Strategy

### Test Organization

```
backend/tests/
├── unit/
│   └── test_csrf.py                    # Existing unit tests (from PR #21)
├── integration/
│   └── test_csrf_routes.py             # Add new tests for logout and chat/send
└── e2e_playwright/
    └── test_csrf_protection.py         # Add critical security scenario tests
```

### Coverage Requirements

- **Unit tests**: Existing CSRF unit tests cover token generation/validation (no changes needed)
- **Integration tests**: Add tests for logout and chat/send endpoints (both positive and negative cases)
- **E2E tests**: Critical security scenarios only:
  - Logout CSRF protection blocks forged requests
  - Chat send CSRF protection blocks forged requests
  - Legitimate logout/chat still works with tokens
  - Token expiration handling for chat interface
- **Overall coverage**: Must maintain 80%+ coverage

### Quality Metrics

- ✅ All tests pass (0 failures)
- ✅ Coverage ≥ 80% (maintained from current baseline)
- ✅ No security scan warnings (Bandit clean)
- ✅ No type checking errors (mypy clean)
- ✅ No linting errors (ruff clean)

---

## Success Criteria

### Functional Requirements

- [ ] `/logout` endpoint validates CSRF token before processing
- [ ] Settings page logout form includes CSRF token
- [ ] Chat page logout form includes CSRF token
- [ ] Logout without valid CSRF token returns 403 and preserves session
- [ ] Logout with valid CSRF token clears session and redirects to login
- [ ] `/chat/send` endpoint validates CSRF token before processing
- [ ] Chat interface JavaScript reads CSRF token from cookie
- [ ] Chat interface sends X-CSRF-Token header with requests
- [ ] Chat interface handles missing token gracefully (clear error message)
- [ ] Chat interface handles expired token with auto-refresh

### Security Requirements

- [ ] Forged logout request (no token) is blocked
- [ ] Forged chat request (no token) is blocked
- [ ] CSRF cookie configuration verified (httponly=false for JavaScript access)
- [ ] CSRF cookie uses SameSite=strict for added protection
- [ ] Token expiration enforced (1 hour max age)
- [ ] Generic error messages prevent user enumeration

### Testing Requirements

- [ ] Integration tests for logout (with/without token, invalid token, expired token)
- [ ] Integration tests for chat/send (with/without token, header validation)
- [ ] E2E test: cross-origin logout attack blocked
- [ ] E2E test: cross-origin chat attack blocked
- [ ] E2E test: legitimate logout works
- [ ] E2E test: legitimate chat message sending works
- [ ] Manual testing: logout forms include visible token in DevTools
- [ ] Manual testing: chat requests include X-CSRF-Token header in Network tab

### Documentation Requirements

- [ ] Parent CSRF specification updated with new protected endpoints
- [ ] Logout protection documented (form-based pattern)
- [ ] Chat send protection documented (header-based pattern)
- [ ] Token expiration handling documented for JavaScript clients

---

## Milestones

### Milestone 1: Logout Protection Complete (Phase 1)
- All logout forms protected with CSRF tokens
- Integration tests passing
- Manual verification successful

### Milestone 2: Chat Protection Complete (Phase 2)
- Chat send endpoint protected
- JavaScript token handling implemented
- Integration and E2E tests passing
- Manual verification successful

### Milestone 3: Documentation & Validation Complete (Phase 3)
- All documentation updated
- Full test suite passing
- Security scan clean
- Ready for final PR to main

---

## Common Commands

```bash
# Development server
./scripts/dev-server.sh

# Local E2E testing environment
./scripts/local-e2e-server.sh  # Start Firestore emulator + dev server

# Run all tests
uv --directory backend run pytest tests/ -v --cov=app

# Run integration tests only
uv --directory backend run pytest tests/integration -v

# Run E2E tests (requires local-e2e-server.sh running)
uv --directory backend run pytest tests/e2e_playwright -v --headed

# Run specific test file
uv --directory backend run pytest tests/integration/test_csrf_routes.py -v

# Code quality checks
uv run ruff check .
uv run ruff format .
uv run mypy backend/app
uv run bandit -c backend/pyproject.toml -r backend/app/ -ll

# Check for CSRF token in templates
grep -rn 'action="/logout"' backend/app/templates/
grep -rn 'fastapi-csrf-token' backend/app/templates/

# Verify CSRF cookie configuration
grep -A5 "cookie_httponly" backend/app/main.py

# Estimate actual hours spent (use when marking phase complete)
git log --oneline chore/csrf-improvements..HEAD --format="%ad" --date=format:"%Y-%m-%d %H:00" | uniq | wc -l
```

---

## Timeline Estimates

### Phase 1: Protect Logout Endpoint (1.5h)
- Setup & branch creation: 5 min
- Write integration tests (TDD): 20 min
- Update backend routes (logout + GET endpoints): 20 min
- Update templates (settings.html + chat.html): 15 min
- Run tests & verify: 10 min
- Manual testing: 10 min
- Commit & PR: 10 min

### Phase 2: Protect Chat Send Endpoint (1.5h)
- Write integration tests (TDD): 25 min
- Update backend route (chat/send): 15 min
- Add JavaScript helper function: 20 min
- Update fetch call with header: 10 min
- Add error handling (missing/expired token): 15 min
- Write E2E tests: 20 min
- Run all tests & verify: 10 min
- Manual testing (DevTools verification): 10 min
- Commit & PR: 5 min

### Phase 3: Documentation & Validation (0.5h)
- Update parent CSRF spec: 15 min
- Run full test suite: 5 min
- Run security scan: 5 min
- Final verification: 5 min

**Total: 3.5 hours**

---

## History

| Date | Event | Branch | Notes |
|------|-------|--------|-------|
| 2025-11-16 | Roadmap created | `chore/csrf-improvements` | Phase planning based on SPECIFICATION.md |
| | Phase 1 plan created | - | Logout endpoint protection |
| | Phase 2 plan created | - | Chat send endpoint protection |
| | Phase 3 plan created | - | Documentation & validation |

---

## Notes

- **Pattern Reuse**: This implementation follows exact patterns from PR #21:
  - Form-based CSRF (like `/auth/login`, `/garmin/link`)
  - Header-based CSRF (like `DELETE /garmin/link`)
- **Cookie Configuration**: Already verified in `backend/app/main.py:53` - `httponly=false` for JavaScript access
- **Infrastructure**: All CSRF protection infrastructure already exists from PR #21
- **Low Risk**: Changes are isolated to 2 endpoints, well-tested patterns, existing infrastructure
- **Quick Wins**: Small, focused phases allow rapid iteration and early feedback

---

**End of Roadmap**
