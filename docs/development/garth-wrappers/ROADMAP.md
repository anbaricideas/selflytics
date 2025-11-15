# Garth Wrappers Implementation Roadmap

**Feature**: Type-safe wrappers for Garth library integration
**GitHub Issue**: [#10 - Eliminate type: ignore comments in Garmin integration](https://github.com/anbaricidias/selflytics/issues/10)
**Specification**: `/Users/bryn/repos/selflytics-garth/docs/development/garth-wrappers/SPECIFICATION.md`
**Status**: Ready for Implementation
**Started**: 2025-11-16
**Branch**: Current branch (feature branch for Garth wrappers)

---

## Executive Summary

This roadmap implements type-safe wrapper functions around the Garth library to eliminate 7+ `type: ignore` comments in the Garmin integration layer. The wrappers provide runtime validation using existing Pydantic models, early detection of API changes, and improved maintainability through explicit type signatures.

**Primary Goals**:
- **Type Safety**: Eliminate all Garth-related `type: ignore` comments (7 locations)
- **Runtime Validation**: Detect Garth API changes before silent data corruption
- **Maintainability**: Clear type signatures for future development

**Security Context**:
- **Critical Pattern**: ALL exception logging MUST use `redact_for_logging()` from telemetry
- **Enforcement**: Pre-commit hooks prevent f-strings in logger calls
- **PII Protection**: Wrapper validation errors contain user data - must be redacted

**Implementation Approach**:
- **TDD workflow**: Write tests first, verify failure, implement, verify pass
- **Model reuse**: Import existing Pydantic models from `app.models.garmin_data`
- **Non-blocking validation**: Log warnings, return raw data (allows recovery from API changes)
- **Minimal disruption**: Internal refactoring only, no user-facing changes

---

## Implementation Strategy

### Core Principles

1. **Type Safety First**: Remove all `type: ignore` comments, pass mypy strict mode
2. **Reuse Existing Models**: Import GarminActivity, DailyMetrics, HealthSnapshot (no duplicates)
3. **Security-Critical Logging**: Use `redact_for_logging()` for all exception/warning logs
4. **Non-Blocking Philosophy**: Validation warnings don't stop execution
5. **TDD Required**: 80%+ coverage, tests before implementation

### Git Workflow

```
[current-branch] (main feature branch)
  ↓
[current-branch]-phase-1 (PR into current branch)
  ↓
[current-branch]-phase-2 (PR into current branch)
  ↓
[current-branch] → main (final PR after all phases complete)
```

**Branch Strategy**:
- Current branch is the main feature branch for this work
- Each phase implemented in a subbranch (e.g., `[current]-phase-1`)
- Subbranches merge into current branch via PR
- Final PR from current branch to `main` after both phases complete

### Session Startup Command

When ready to implement each phase:

```
I'm continuing work on Garth Wrappers from the roadmap at @docs/development/garth-wrappers/ROADMAP.md

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
| [1](./PHASE_1_plan.md) | Wrapper Implementation & Integration | ⏳ NEXT | `[current]-phase-1` | 1.5h | - |
| [2](./PHASE_2_plan.md) | Testing & Quality Assurance | 📅 PENDING | `[current]-phase-2` | 1.5h | - |

**Current Phase**: ⏳ Phase 1 ready to start

**Total Estimated Time**: 3 hours across 2 phases

---

## Dependencies

### Required Packages (Already Installed)

No new dependencies required - uses existing libraries:
- `garth` - Garmin Connect integration (already installed)
- `pydantic` - Model validation (already installed)
- `telemetry` - Logging utilities with PII redaction (workspace package)

### Existing Models (To Import)

Located in `backend/app/models/garmin_data.py`:
- `GarminActivity` - Activity validation with field aliases
- `DailyMetrics` - Daily summary validation
- `HealthSnapshot` - Health snapshot validation

---

## Testing Strategy

### Test Distribution by Phase

**Phase 1**: Wrapper Implementation & Integration
- Unit tests: Wrapper module (token ops + data retrieval)
- Integration tests: Verify wrappers called by clients
- Target coverage: 90%+ on wrapper module, 80%+ overall

**Phase 2**: Testing & Quality Assurance
- Run full test suite (verify no regressions)
- Type checking: Mypy passes on all files
- Code quality: Ruff, bandit, formatting
- Manual verification: Grep for remaining type: ignore comments

### TDD Workflow (Every Phase)

1. **Write Tests First**: Define expected behavior with test cases
2. **Review Tests**: Ensure quality (if test-quality-reviewer available)
3. **Verify Failure**: Run tests, confirm they fail (no implementation yet)
4. **Implement**: Write minimal code to pass tests
5. **Verify Success**: Run tests, confirm they pass
6. **Commit**: Save progress with clear commit message

### Coverage Requirements

- **Minimum**: 80% coverage on all code (enforced by CI)
- **Target**: 90%+ coverage on wrapper module (security-critical)
- **Enforcement**: CI fails if coverage drops below threshold

### Test Organization

```
backend/tests/
├── unit/
│   └── test_garth_wrapper.py        # NEW - Wrapper unit tests (90%+ coverage)
└── integration/
    ├── test_garmin_client.py         # UPDATED - Verify wrappers used
    └── test_garmin_oauth.py          # UPDATED - Verify token wrappers used
```

**Note**: No new E2E tests required - this is internal refactoring. Existing E2E tests in `tests/e2e_playwright/` must continue passing without modification.

---

## Quality Gates

### Per-Phase Quality Checks

Before marking a phase complete:

1. **Code Quality**:
   - [ ] `uv run ruff check .` passes with no errors
   - [ ] `uv run ruff format --check .` passes
   - [ ] All imports at top of files (no function-level imports)
   - [ ] No f-strings in logger calls (PII protection)

2. **Testing**:
   - [ ] All new tests passing (unit + integration)
   - [ ] All existing tests still passing (no regressions)
   - [ ] 80%+ coverage maintained across codebase
   - [ ] 90%+ coverage on `garth_wrapper.py`

3. **Security**:
   - [ ] `uv run bandit -c backend/pyproject.toml -r backend/app/ -ll` passes
   - [ ] All exception logging uses `redact_for_logging()`
   - [ ] No PII in validation warning messages

4. **Type Safety**:
   - [ ] `uv --directory backend run mypy backend/app/services/garth_wrapper.py --strict` passes
   - [ ] `uv --directory backend run mypy backend/app/services/garmin_client.py` passes
   - [ ] `uv --directory backend run mypy backend/app/services/garmin_service.py` passes
   - [ ] Grep finds no Garth-related `type: ignore` comments

5. **Documentation**:
   - [ ] Phase plan updated with completion status
   - [ ] All implementation steps marked ✅ DONE
   - [ ] Commit messages follow conventional commits format

### Final Quality Gate (Before PR to main)

- [ ] Both phases complete
- [ ] All quality gates passed
- [ ] Type checking passes on all affected files
- [ ] No Garth-related `type: ignore` comments remain
- [ ] All 7 original locations updated with typed wrappers
- [ ] No failing tests anywhere in codebase

---

## Affected Code Locations

### Files to Create

| File | Purpose | Lines | Tests |
|------|---------|-------|-------|
| `backend/app/services/garth_wrapper.py` | Typed wrapper functions | ~470 | Yes |
| `backend/tests/unit/test_garth_wrapper.py` | Wrapper unit tests | ~250 | - |

### Files to Update

| File | Changes | Type: Ignore Removals |
|------|---------|----------------------|
| `backend/app/services/garmin_client.py` | Import wrappers, update 7 locations | Lines 79, 80, 96, 97, 156, 200, 227 |
| `backend/app/services/garmin_service.py` | Import wrapper, update 1 location | Line 198 |
| `backend/tests/integration/test_garmin_client.py` | Add wrapper verification tests | - |

**Total Type: Ignore Removals**: 8 (7 in garmin_client.py, 1 in garmin_service.py)

**Verification Command**:
```bash
# Before: Should find 8 Garth-related type: ignore comments
grep -n "type: ignore" backend/app/services/garmin_client.py backend/app/services/garmin_service.py | grep -E "(garth|oauth|activities|daily_summary|health_snapshot|profile)"

# After: Should find zero Garth-related type: ignore comments
```

---

## Success Criteria

### Phase 1 Success Criteria

**Technical Success**:
- [ ] `backend/app/services/garth_wrapper.py` exists with all functions implemented
- [ ] Token operation wrappers (get/set oauth1/oauth2, get profile)
- [ ] Data retrieval wrappers (activities, daily_summary, health_snapshot)
- [ ] All wrappers have complete docstrings (Args/Returns/Raises/Note)
- [ ] garmin_client.py uses wrappers (7 locations updated)
- [ ] garmin_service.py uses wrappers (1 location updated)
- [ ] All Garth-related `type: ignore` comments removed

**Quality Metrics**:
- [ ] Unit tests written and passing
- [ ] Integration tests verify wrappers called
- [ ] Code quality checks passing
- [ ] All imports at file top

### Phase 2 Success Criteria

**Technical Success**:
- [ ] All tests passing (unit, integration, e2e)
- [ ] Mypy passes with `--strict` on wrapper module
- [ ] Mypy passes on garmin_client.py and garmin_service.py
- [ ] No Garth-related `type: ignore` comments found via grep
- [ ] Coverage ≥90% on wrapper module
- [ ] Coverage ≥80% overall maintained

**Quality Metrics**:
- [ ] Ruff linting passes
- [ ] Ruff formatting passes
- [ ] Bandit security scan passes
- [ ] All exception logs use `redact_for_logging()`

---

## Common Commands

### Development

```bash
# Sync dependencies (no new packages needed)
uv sync --all-extras

# Run development server
./scripts/dev-server.sh

# Run all tests
uv --directory backend run pytest tests/ -v --cov=app

# Run specific test categories
uv --directory backend run pytest tests/unit -v              # Unit tests only
uv --directory backend run pytest tests/integration -v       # Integration tests

# Check coverage on wrapper module
uv --directory backend run pytest tests/unit/test_garth_wrapper.py -v \
  --cov=app.services.garth_wrapper --cov-report=term-missing --cov-fail-under=90
```

### Type Checking

```bash
# Verify wrapper module passes strict mode
uv --directory backend run mypy backend/app/services/garth_wrapper.py --strict

# Verify integration files pass mypy
uv --directory backend run mypy backend/app/services/garmin_client.py
uv --directory backend run mypy backend/app/services/garmin_service.py

# Search for remaining type: ignore comments
grep -n "type: ignore" backend/app/services/garmin_client.py backend/app/services/garmin_service.py
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
uv run bandit -c backend/pyproject.toml -r backend/app/services/garth_wrapper.py -ll

# Verify no f-strings in logging
grep -n 'logger.*f"' backend/app/services/garth_wrapper.py
```

### Git Workflow

```bash
# Create phase 1 branch (from current branch)
git checkout -b [current-branch]-phase-1

# Commit after each step
git add .
git commit -m "test: Add unit tests for OAuth token wrappers"
git commit -m "feat: Implement typed Garth wrapper functions"
git commit -m "refactor: Update garmin_client to use typed wrappers"

# Push phase branch
git push -u origin [current-branch]-phase-1

# Create PR into current branch (via GitHub UI)
gh pr create --base [current-branch] --title "Phase 1: Wrapper Implementation & Integration"

# After PR merge, continue with next phase
git checkout [current-branch]
git pull origin [current-branch]
git checkout -b [current-branch]-phase-2
```

### Hours Estimate

```bash
# Calculate actual hours spent on branch
git log --oneline main..HEAD --format="%ad" --date=format:"%Y-%m-%d %H:00" | uniq | wc -l
```

---

## Risk Mitigation

### Technical Risks

**Risk**: Validation models don't match actual Garth response structure
- **Mitigation**: Reuse existing models already validated against Garth
- **Mitigation**: Non-blocking validation (log warning, return raw data)
- **Mitigation**: Integration tests use real Garth response structures from existing tests

**Risk**: Breaking existing Garmin functionality during refactoring
- **Mitigation**: TDD approach ensures tests validate expected behavior
- **Mitigation**: All existing tests must continue passing
- **Mitigation**: Integration tests verify wrappers actually called

**Risk**: Mypy errors too strict, blocking completion
- **Mitigation**: Wrapper module uses `dict[str, Any]` return types (pragmatic)
- **Mitigation**: Only wrapper module requires `--strict` mode
- **Mitigation**: Integration files just need to pass standard mypy (no --strict)

### Process Risks

**Risk**: PII accidentally logged during validation errors
- **Mitigation**: Every logger call uses `redact_for_logging()`
- **Mitigation**: Pre-commit hooks enforce no f-strings in logs
- **Mitigation**: Bandit security scan in Phase 2

**Risk**: Coverage drops during refactoring
- **Mitigation**: Write comprehensive unit tests (90%+ on wrapper)
- **Mitigation**: Integration tests verify usage
- **Mitigation**: CI enforces 80%+ coverage threshold

---

## Timeline Estimate

| Phase | Focus | Duration | Cumulative |
|-------|-------|----------|------------|
| **Phase 1** | Implementation & Integration | 1.5h | 1.5h |
| **Phase 2** | Testing & Quality Assurance | 1.5h | 3h |
| **TOTAL** | | **3 hours** | - |

**Assumptions**:
- TDD workflow followed (may add overhead)
- No unexpected Garth API incompatibilities
- Existing Pydantic models work as expected
- All 7 type: ignore locations straightforward to replace

---

## History

| Date | Event | Notes |
|------|-------|-------|
| 2025-11-16 | Specification finalized | SPECIFICATION.md v1.1 (includes security fixes) |
| 2025-11-16 | Roadmap created | 2 consolidated phases, 1-hour sessions, skip E2E tests |
| 2025-11-16 | Ready for implementation | Phase 1 next |

---

## References

**Project Documentation**:
- [Garth Wrappers Specification](./SPECIFICATION.md) - Complete technical specification
- [Project CLAUDE.md](../../../.claude/CLAUDE.md) - Development workflow and conventions
- [Main Roadmap](../../project-setup/ROADMAP.md) - Overall project progress
- [Development Workflow](../../DEVELOPMENT_WORKFLOW.md) - TDD patterns and testing practices

**Standards & Best Practices**:
- [PEP 561 - Distributing Type Information](https://www.python.org/dev/peps/pep-0561/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [Mypy Documentation](https://mypy.readthedocs.io/)

**Related Issues**:
- [GitHub Issue #10](https://github.com/anbaricidias/selflytics/issues/10) - Type safety for Garth integration

**Reference Projects**:
- CliniCraft - `/Users/bryn/repos/clinicraft/` (telemetry patterns, Pydantic-AI)
- Garmin Agents - `/Users/bryn/repos/garmin_agents/` (Garth integration patterns)

---

*Last Updated: 2025-11-16*
*Status: Ready for Implementation*
