# CSRF Protection Implementation Roadmap

**Feature**: Add CSRF protection to all POST forms
**GitHub Issue**: [#8 - Add CSRF protection to all POST forms](https://github.com/anbaricidias/selflytics/issues/8)
**Specification**: `/Users/bryn/repos/selflytics-csrf/docs/development/csrf/CSRF_SPECIFICATION.md`
**Status**: Ready for Implementation
**Started**: 2025-11-15
**Branch**: `feat/csrf`

---

## Executive Summary

This roadmap implements comprehensive Cross-Site Request Forgery (CSRF) protection for Selflytics using the `fastapi-csrf-protect` library. The protection uses the **Double Submit Cookie pattern** to secure all state-changing POST endpoints while maintaining seamless HTMX compatibility.

**Security Context**:
- **Current Vulnerability**: Cookie-based authentication with `samesite="lax"` is insufficient protection
- **Attack Surface**: 4 POST endpoints vulnerable to CSRF attacks
- **Highest Risk**: `/garmin/link` endpoint (account linking vulnerability)
- **Impact**: Account confusion, privacy violations, service disruption

**Implementation Approach**:
- TDD workflow: Write tests first, verify failure, implement, verify pass
- Integrated testing: Tests written and executed within each phase
- Critical E2E coverage: Focus on high-risk scenarios (attack prevention, token rotation)
- HTMX compatibility: Token rotation on form re-render, partial DOM update support

---

## Implementation Strategy

### Core Principles

1. **Security First**: Protect against real-world attack scenarios from specification
2. **TDD Workflow**: Write tests before implementation in every phase
3. **HTMX Compatibility**: Ensure token rotation works with partial DOM updates
4. **Privacy Protection**: Generic error messages prevent user enumeration
5. **Minimal Disruption**: No changes to user experience (tokens invisible)

### Git Workflow

```
main
  ↓
feat/csrf (core feature branch)
  ↓
feat/csrf-phase-1 (PR into feat/csrf)
  ↓
feat/csrf-phase-2 (PR into feat/csrf)
  ↓
feat/csrf-phase-3 (PR into feat/csrf)
  ↓
feat/csrf → main (final PR)
```

**Branch Strategy**:
- Each phase implemented in a sub-branch (e.g., `feat/csrf-phase-1`)
- Sub-branches merge into `feat/csrf` via PR
- Final `feat/csrf` merges into `main` after all phases complete

### Session Startup Command

When ready to implement each phase:

```
I'm continuing work on CSRF protection from the roadmap at @docs/development/csrf/ROADMAP.md

Guidelines:
1. Follow the phase planning document as single source of truth
2. Use TDD: write tests first, verify failure, implement, verify pass
3. Commit after each major step with clear commit messages
4. Follow CLAUDE.md guidelines (imports at top, uv for dependencies, PII redaction)
5. Track progress in phase plan checkboxes only
6. Ask questions only if blocked or contradictory info found

Start from: wherever marked as ⏳ NEXT
```

---

## Phase Overview

| Phase | Description | Status | Branch | Estimated | Actual |
|-------|-------------|--------|--------|-----------|--------|
| [1](./PHASE_1_plan.md) | CSRF Infrastructure & Auth Routes | ✅ DONE | `feat/csrf-1` | 2h | ~5h |
| [2](./PHASE_2_plan.md) | Garmin Routes CSRF Protection | ⏳ NEXT | `feat/csrf-phase-2` | 1.5h | - |
| [3](./PHASE_3_plan.md) | E2E Tests & Security Validation | 📅 PLANNED | `feat/csrf-phase-3` | 1.5h | - |

**Current Phase**: Phase 2 (Garmin Routes CSRF Protection)

**Total Estimated Time**: 5 hours across 3 phases

---

## Dependencies

### Required Packages (To Install)

```bash
# Add CSRF protection library
uv add fastapi-csrf-protect
```

### Environment Variables (To Configure)

Add to `backend/.env.example`:
```bash
# CSRF Protection
CSRF_SECRET="change-this-in-production-min-32-chars"
```

Add to `backend/.env`:
```bash
# CSRF Protection (dev environment)
CSRF_SECRET="dev-csrf-secret-change-in-production-min-32-chars-for-security"
```

### Configuration Updates Required

- `backend/app/config.py` - Add `csrf_secret` field to Settings class
- `backend/app/main.py` - Configure CsrfProtect and exception handler
- `backend/app/templates/fragments/csrf_error.html` - New error template

---

## Testing Strategy

### Test Distribution by Phase

**Phase 1**: CSRF Infrastructure & Auth Routes
- Unit tests: CSRF token generation, validation, expiration
- Integration tests: /auth/register and /auth/login protection
- Coverage: CSRF configuration, auth route protection

**Phase 2**: Garmin Routes CSRF Protection
- Unit tests: Token rotation logic
- Integration tests: /garmin/link and /garmin/sync protection
- Coverage: Garmin route protection, error handling

**Phase 3**: E2E Tests & Security Validation
- E2E tests: Attack prevention (cross-origin POST blocked)
- E2E tests: Token rotation on validation errors
- E2E tests: HTMX partial update compatibility
- Security: Bandit scan passes
- Manual: Runsheet execution

### TDD Workflow (Every Phase)

1. **Write Tests First**: Define expected behavior with test cases
2. **Verify Failure**: Run tests, confirm they fail (no implementation yet)
3. **Implement**: Write minimal code to pass tests
4. **Verify Success**: Run tests, confirm they pass
5. **Refactor**: Clean up code while keeping tests green
6. **Commit**: Save progress with clear commit message

### Coverage Requirements

- **Minimum**: 80% coverage on all new code
- **Enforcement**: CI fails if coverage drops below threshold
- **Target**: 90%+ coverage for security-critical code (CSRF validation)

### Test Organization

```
backend/tests/
├── unit/
│   └── test_csrf.py              # CSRF token generation/validation
├── integration/
│   └── test_csrf_routes.py       # Protected route integration tests
└── e2e_playwright/
    └── test_csrf_e2e.py          # Attack prevention, token rotation
```

---

## Quality Gates

### Per-Phase Quality Checks

Before marking a phase complete:

1. **Code Quality**:
   - [ ] `uv run ruff check .` passes with no errors
   - [ ] `uv run ruff format --check .` passes
   - [ ] All imports at top of files (no function-level imports)

2. **Testing**:
   - [ ] All new tests passing (unit + integration)
   - [ ] 80%+ coverage on new code
   - [ ] Tests follow TDD pattern (written before implementation)

3. **Security**:
   - [ ] `uv run bandit -c backend/pyproject.toml -r backend/app/ -ll` passes
   - [ ] No PII logged (use `redact_for_logging` utility)
   - [ ] CSRF tokens have sufficient entropy (32+ characters)

4. **Documentation**:
   - [ ] Phase plan updated with completion status
   - [ ] All implementation steps marked ✅ DONE
   - [ ] Commit messages follow conventional commits format

5. **Manual Validation** (Phase-specific):
   - See individual phase plans for specific checks

### Final Quality Gate (Before PR to main)

- [ ] All 3 phases complete
- [ ] All quality gates passed
- [ ] E2E tests passing (attack prevention verified)
- [ ] Manual runsheet completed
- [ ] Documentation updated
- [ ] No failing tests anywhere in codebase

---

## Protected Endpoints

### Priority 1: HIGH RISK (Phase 2)

| Endpoint | Method | Current Risk | Protection Added |
|----------|--------|--------------|------------------|
| `/garmin/link` | POST | **HIGH** - Account linking attack | Phase 2 |
| `/garmin/sync` | POST | Medium - Unwanted data sync | Phase 2 |

### Priority 2: MEDIUM RISK (Phase 1)

| Endpoint | Method | Current Risk | Protection Added |
|----------|--------|--------------|------------------|
| `/auth/register` | POST | Medium - Spam accounts | Phase 1 |
| `/auth/login` | POST | Medium - Session fixation | Phase 1 |

---

## Success Criteria

### Phase 1 Success Criteria

**Technical Success**:
- [ ] fastapi-csrf-protect installed and configured
- [ ] CSRF exception handler returns appropriate responses (403 HTML/JSON)
- [ ] /auth/register requires valid CSRF token
- [ ] /auth/login requires valid CSRF token
- [ ] Tokens rotated on validation errors
- [ ] Unit tests pass (token generation, validation)
- [ ] Integration tests pass (auth routes protected)

**Quality Metrics**:
- [ ] 80%+ test coverage on CSRF configuration
- [ ] Ruff linting passes
- [ ] Bandit security scan passes

### Phase 2 Success Criteria

**Technical Success**:
- [ ] /garmin/link requires valid CSRF token (HIGH PRIORITY)
- [ ] /garmin/sync requires valid CSRF token
- [ ] Garmin templates include hidden csrf_token fields
- [ ] Token rotation works on Garmin link errors
- [ ] Integration tests pass (Garmin routes protected)

**Quality Metrics**:
- [ ] 80%+ test coverage on Garmin CSRF protection
- [ ] All quality gates pass

### Phase 3 Success Criteria

**Technical Success**:
- [ ] E2E test: Cross-origin POST attack blocked (Garmin link scenario)
- [ ] E2E test: Token rotation on validation error
- [ ] E2E test: HTMX partial updates preserve CSRF tokens
- [ ] Manual runsheet completed (all scenarios pass)
- [ ] Security scan passes (bandit)

**Quality Metrics**:
- [ ] 80%+ overall test coverage maintained
- [ ] All E2E tests passing
- [ ] Zero security vulnerabilities detected

---

## Common Commands

### Development

```bash
# Install dependencies (after adding fastapi-csrf-protect)
uv sync --all-extras

# Run development server
./scripts/dev-server.sh

# Run all tests
uv --directory backend run pytest tests/ -v --cov=app

# Run specific test categories
uv --directory backend run pytest tests/unit -v              # Unit tests only
uv --directory backend run pytest tests/integration -v       # Integration tests
uv --directory backend run pytest tests/e2e_playwright -v    # E2E tests

# Check coverage
uv --directory backend run pytest --cov=app --cov-report=term-missing --cov-report=html
```

### Code Quality

```bash
# Format code
uv run ruff format .
uv run ruff check --fix .

# Check code quality (CI checks)
uv run ruff check .
uv run ruff format --check .

# Security scan
uv run bandit -c backend/pyproject.toml -r backend/app/ -ll
```

### Git Workflow

```bash
# Create phase branch (from feat/csrf)
git checkout feat/csrf
git checkout -b feat/csrf-phase-1

# Commit after each step
git add .
git commit -m "test: Add CSRF token validation unit tests"
git commit -m "feat: Configure CSRF protection in main.py"

# Push phase branch
git push -u origin feat/csrf-phase-1

# Create PR into feat/csrf (via GitHub UI)
gh pr create --base feat/csrf --title "Phase 1: CSRF Infrastructure & Auth Routes"

# After PR merge, continue with next phase
git checkout feat/csrf
git pull origin feat/csrf
git checkout -b feat/csrf-phase-2
```

### Hours Estimate

```bash
# Calculate actual hours spent on branch
git log --oneline feat/csrf..HEAD --format="%ad" --date=format:"%Y-%m-%d %H:00" | uniq | wc -l
```

---

## Risk Mitigation

### Technical Risks

**Risk**: CSRF library incompatible with HTMX partial updates
- **Mitigation**: Token rotation pattern tested in Phase 1 auth routes first
- **Mitigation**: Specification includes detailed HTMX integration guidance
- **Mitigation**: E2E tests verify HTMX compatibility in Phase 3

**Risk**: Breaking existing authentication flows
- **Mitigation**: Comprehensive integration tests before and after changes
- **Mitigation**: TDD approach ensures tests validate expected behavior
- **Mitigation**: Manual testing runsheet validates user journeys

**Risk**: Token expiration disrupts user experience
- **Mitigation**: 1-hour token expiration (configurable)
- **Mitigation**: Token automatically rotated on validation errors
- **Mitigation**: Generic error messages guide users to retry

### Process Risks

**Risk**: E2E tests brittle or flaky
- **Mitigation**: Focus on critical paths only (not comprehensive coverage)
- **Mitigation**: Use stable selectors (data-testid attributes)
- **Mitigation**: Clear debugging guides and screenshots on failure

**Risk**: Security vulnerabilities introduced during implementation
- **Mitigation**: Bandit security scan in every phase
- **Mitigation**: Follow specification's security patterns exactly
- **Mitigation**: PII redaction enforced by pre-commit hooks

---

## Timeline Estimate

| Phase | Duration | Effort (hours) | Cumulative |
|-------|----------|----------------|------------|
| **Phase 1** | 1 session | 2 | 2 |
| **Phase 2** | 1 session | 1.5 | 3.5 |
| **Phase 3** | 1 session | 1.5 | 5 |
| **TOTAL** | **3 sessions** | **5 hours** | - |

**Assumptions**:
- TDD workflow followed strictly (may add 20% overhead)
- No major HTMX compatibility issues discovered
- Specification patterns work as documented

---

## History

| Date | Event | Notes |
|------|-------|-------|
| 2025-11-15 | Roadmap created | 3 phases, TDD with integrated testing, critical E2E coverage |
| 2025-11-15 | Specification finalized | CSRF_SPECIFICATION.md v1.0 |
| 2025-11-15 | Branch created | feat/csrf (from main) |
| 2025-11-15 | Phase 1 completed | CSRF Infrastructure & Auth Routes (~5 hours, 8 commits, 341 tests passing) |

---

## References

**Project Documentation**:
- [CSRF Specification](./CSRF_SPECIFICATION.md) - Complete security specification
- [Project CLAUDE.md](../../../.claude/CLAUDE.md) - Development workflow and conventions
- [Main Roadmap](../../project-setup/ROADMAP.md) - Overall project progress

**Standards & Best Practices**:
- [OWASP CSRF Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html)
- [fastapi-csrf-protect Documentation](https://github.com/aekasitt/fastapi-csrf-protect)
- [HTMX Security](https://htmx.org/docs/#security)

**Related Issues**:
- [GitHub Issue #8](https://github.com/anbaricidias/selflytics/issues/8) - Add CSRF protection to all POST forms

---

*Last Updated: 2025-11-15*
*Status: Ready for Implementation*
