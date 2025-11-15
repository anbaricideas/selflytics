# Phase 2: Testing & Quality Assurance

**Branch**: `[current-branch]-phase-2`
**Status**: 📅 PENDING
**Estimated Time**: 1.5 hours
**Actual Time**: -
**Started**: -
**Completed**: -

---

## Goal

Comprehensive verification of type safety improvements, test coverage, code quality, and security compliance. This phase ensures all Garth-related `type: ignore` comments are eliminated, mypy passes on all affected files, and the implementation meets project quality standards.

**Key Deliverables**:
- Mypy passes with `--strict` on `garth_wrapper.py`
- Mypy passes on `garmin_client.py` and `garmin_service.py`
- Zero Garth-related `type: ignore` comments found via grep
- All tests passing (unit, integration, e2e)
- 90%+ coverage on wrapper module, 80%+ overall
- All code quality checks passing (ruff, bandit, formatting)
- Documentation updated with completion status

**Quality Impact**:
- Type safety verified across Garmin integration layer
- Security compliance confirmed (PII redaction, no vulnerabilities)
- Test coverage maintained above project thresholds
- Code quality standards met

---

## Prerequisites

**Required Before Starting**:
- [ ] Phase 1 complete and merged into current branch
- [ ] All Phase 1 deliverables verified
- [ ] Current branch checked out and up to date
- [ ] No failing tests in codebase

**Phase 1 Completion Checklist**:
- [ ] `backend/app/services/garth_wrapper.py` exists with all functions
- [ ] `backend/tests/unit/test_garth_wrapper.py` exists with comprehensive tests
- [ ] `garmin_client.py` updated (7 locations)
- [ ] `garmin_service.py` updated (1 location)
- [ ] All unit and integration tests passing
- [ ] Basic coverage checks complete

---

## Deliverables

### Modified Files
- [ ] `docs/development/garth-wrappers/ROADMAP.md` - Update phase status
- [ ] `docs/development/garth-wrappers/PHASE_1_plan.md` - Mark complete
- [ ] `docs/development/garth-wrappers/PHASE_2_plan.md` - Mark complete

### Verification Artifacts
- [ ] Mypy output logs (all files pass)
- [ ] Coverage report (90%+ wrapper, 80%+ overall)
- [ ] Grep output (zero Garth-related type: ignore)
- [ ] Code quality reports (ruff, bandit clean)

---

## Implementation Steps

### Setup

- [ ] ⏳ NEXT: Create phase 2 branch from current branch
  ```bash
  git checkout [current-branch]
  git pull origin [current-branch]  # Get Phase 1 changes
  git checkout -b [current-branch]-phase-2
  ```

---

### Step 1: Type Checking - Wrapper Module (Strict Mode)

**Goal**: Verify wrapper module passes mypy with strict mode enabled

**File**: `backend/app/services/garth_wrapper.py`

#### Verification

- [ ] Run mypy in strict mode on wrapper module
  ```bash
  uv --directory backend run mypy backend/app/services/garth_wrapper.py --strict
  ```

#### Fix Any Issues (if needed)

- [ ] If mypy errors found, analyse and fix:
  - [ ] Check all function signatures have type hints
  - [ ] Verify return types are explicit (`dict[str, Any]`, not implicit)
  - [ ] Ensure no `Any` used without justification
  - [ ] Check all parameters have type annotations

- [ ] Common fixes for strict mode:
  ```python
  # Missing return type
  def get_oauth1_token() -> dict[str, Any]:  # Add explicit return type
      ...

  # Untyped parameter
  def set_oauth1_token(token: dict[str, Any]) -> None:  # Add parameter type
      ...
  ```

- [ ] Re-run mypy until clean
  ```bash
  uv --directory backend run mypy backend/app/services/garth_wrapper.py --strict
  ```

- [ ] Commit any fixes
  ```bash
  git add backend/app/services/garth_wrapper.py
  git commit -m "fix: Add type annotations for mypy strict mode compliance"
  ```

**Success Criteria**:
- [ ] Mypy strict mode passes with zero errors
- [ ] No warnings about missing type annotations
- [ ] All function signatures have explicit return types
- [ ] All parameters have type hints

**Reference**: Spec lines 807-824 (mypy verification)

---

### Step 2: Type Checking - Integration Files

**Goal**: Verify `garmin_client.py` and `garmin_service.py` pass mypy

**Files**:
- `backend/app/services/garmin_client.py`
- `backend/app/services/garmin_service.py`

#### Verification

- [ ] Run mypy on garmin_client.py
  ```bash
  uv --directory backend run mypy backend/app/services/garmin_client.py
  ```

- [ ] Run mypy on garmin_service.py
  ```bash
  uv --directory backend run mypy backend/app/services/garmin_service.py
  ```

#### Fix Any Issues (if needed)

- [ ] If mypy errors found related to wrapper usage:
  - [ ] Check wrapper imports are correct
  - [ ] Verify wrapper return types match expected usage
  - [ ] Ensure `asyncio.to_thread()` calls properly typed

- [ ] Re-run mypy until both files clean
  ```bash
  uv --directory backend run mypy backend/app/services/garmin_client.py backend/app/services/garmin_service.py
  ```

- [ ] Commit any fixes
  ```bash
  git add backend/app/services/garmin_client.py backend/app/services/garmin_service.py
  git commit -m "fix: Resolve mypy type checking issues"
  ```

**Success Criteria**:
- [ ] Mypy passes on garmin_client.py with zero errors
- [ ] Mypy passes on garmin_service.py with zero errors
- [ ] No Garth-related type errors
- [ ] Wrapper usage properly typed

**Reference**: Spec lines 810-815 (mypy on integration files)

---

### Step 3: Verify Type: Ignore Removal

**Goal**: Confirm all Garth-related `type: ignore` comments eliminated

#### Verification

- [ ] Search for type: ignore in garmin_client.py
  ```bash
  grep -n "type: ignore" backend/app/services/garmin_client.py
  ```
  **Expected**: No Garth-related occurrences (oauth, activities, daily_summary, health_snapshot)

- [ ] Search for type: ignore in garmin_service.py
  ```bash
  grep -n "type: ignore" backend/app/services/garmin_service.py
  ```
  **Expected**: No Garth-related occurrences (profile)

- [ ] Search specifically for Garth-related type: ignore
  ```bash
  grep -n "type: ignore" backend/app/services/garmin_client.py backend/app/services/garmin_service.py | grep -E "(garth|oauth|activities|daily_summary|health_snapshot|profile)"
  ```
  **Expected**: Empty output (zero matches)

- [ ] Document verification results
  ```bash
  # Save output for PR description
  grep -n "type: ignore" backend/app/services/garmin_client.py backend/app/services/garmin_service.py > /tmp/type_ignore_check.txt
  ```

**Success Criteria**:
- [ ] Zero Garth-related `type: ignore` comments in garmin_client.py
- [ ] Zero Garth-related `type: ignore` comments in garmin_service.py
- [ ] Any remaining `type: ignore` comments are unrelated to Garth integration
- [ ] All 8 original type: ignore locations eliminated (7 in garmin_client.py, 1 in garmin_service.py)

**Reference**: Spec lines 816-824 (grep verification)

---

### Step 4: Test Coverage Verification

**Goal**: Ensure 90%+ coverage on wrapper module, 80%+ overall

#### Verification

- [ ] Check wrapper module coverage
  ```bash
  uv --directory backend run pytest backend/tests/unit/test_garth_wrapper.py -v \
    --cov=app.services.garth_wrapper --cov-report=term-missing --cov-fail-under=90
  ```
  **Expected**: Passes with 90%+ coverage

- [ ] Check overall test coverage
  ```bash
  uv --directory backend run pytest tests/ -v --cov=app --cov-report=term-missing --cov-fail-under=80
  ```
  **Expected**: Passes with 80%+ coverage

- [ ] Generate HTML coverage report for detailed review
  ```bash
  uv --directory backend run pytest tests/ --cov=app --cov-report=html
  # Review at backend/htmlcov/index.html
  ```

#### Fix Coverage Gaps (if needed)

- [ ] If wrapper module coverage <90%:
  - [ ] Identify uncovered lines in report
  - [ ] Add tests for missing scenarios
  - [ ] Re-run until 90%+ achieved

- [ ] If overall coverage <80%:
  - [ ] Check if wrapper changes affected existing coverage
  - [ ] Add missing tests
  - [ ] Re-run until 80%+ achieved

- [ ] Commit any additional tests
  ```bash
  git add backend/tests/unit/test_garth_wrapper.py
  git commit -m "test: Add additional tests to meet 90% coverage threshold"
  ```

**Success Criteria**:
- [ ] Wrapper module coverage ≥90%
- [ ] Overall test coverage ≥80%
- [ ] Coverage report shows all critical paths tested
- [ ] No significant coverage regressions from baseline

**Reference**: Spec lines 867-871, 901 (coverage requirements)

---

### Step 5: Run Full Test Suite

**Goal**: Verify all tests passing (unit, integration, e2e)

#### Verification

- [ ] Run all unit tests
  ```bash
  uv --directory backend run pytest tests/unit -v
  ```
  **Expected**: All passing

- [ ] Run all integration tests
  ```bash
  uv --directory backend run pytest tests/integration -v
  ```
  **Expected**: All passing

- [ ] Run all e2e tests (verify no regressions)
  ```bash
  # Terminal 1: Start local environment
  ./scripts/local-e2e-server.sh

  # Terminal 2: Run e2e tests
  uv --directory backend run pytest tests/e2e_playwright -v
  ```
  **Expected**: All passing (no changes to e2e tests, internal refactoring only)

- [ ] Run complete test suite with coverage
  ```bash
  uv --directory backend run pytest tests/ -v --cov=app
  ```

#### Fix Test Failures (if any)

- [ ] If unit test failures:
  - [ ] Analyse failure output
  - [ ] Fix wrapper implementation or test logic
  - [ ] Re-run until passing

- [ ] If integration test failures:
  - [ ] Check wrapper mocking in tests
  - [ ] Verify wrapper imports correct
  - [ ] Re-run until passing

- [ ] If e2e test failures:
  - [ ] Should NOT occur (internal refactoring only)
  - [ ] If failures found, investigate wrapper behaviour changes
  - [ ] Fix to maintain exact same external behaviour

- [ ] Commit any fixes
  ```bash
  git add .
  git commit -m "fix: Resolve test failures from wrapper integration"
  ```

**Success Criteria**:
- [ ] All unit tests passing
- [ ] All integration tests passing
- [ ] All e2e tests passing (unchanged from baseline)
- [ ] Zero test failures anywhere in codebase
- [ ] Test suite completes without errors

**Reference**: Spec lines 869-871 (all tests passing requirement)

---

### Step 6: Code Quality Checks

**Goal**: Verify linting, formatting, and security standards met

#### Ruff Linting

- [ ] Run ruff linter
  ```bash
  uv run ruff check .
  ```
  **Expected**: Zero errors

- [ ] Fix any linting issues
  ```bash
  uv run ruff check --fix .
  ```

- [ ] Re-run to verify clean
  ```bash
  uv run ruff check .
  ```

#### Ruff Formatting

- [ ] Check code formatting
  ```bash
  uv run ruff format --check .
  ```
  **Expected**: All files properly formatted

- [ ] Fix formatting if needed
  ```bash
  uv run ruff format .
  ```

- [ ] Re-check
  ```bash
  uv run ruff format --check .
  ```

#### Security Scan

- [ ] Run bandit security scanner on wrapper module
  ```bash
  uv run bandit -c backend/pyproject.toml -r backend/app/services/garth_wrapper.py -ll
  ```
  **Expected**: No issues found

- [ ] Run bandit on full app (verify no new vulnerabilities)
  ```bash
  uv run bandit -c backend/pyproject.toml -r backend/app/ -ll
  ```
  **Expected**: No new issues introduced

#### PII Redaction Verification

- [ ] Verify no f-strings in logger calls
  ```bash
  grep -n 'logger.*f"' backend/app/services/garth_wrapper.py
  ```
  **Expected**: Empty output

- [ ] Manually review all logger calls use `redact_for_logging()`
  ```bash
  grep -n 'logger\.' backend/app/services/garth_wrapper.py
  ```
  **Expected**: All logger calls use `redact_for_logging(str(e))` pattern

#### Fix Issues (if any)

- [ ] Commit any code quality fixes
  ```bash
  git add .
  git commit -m "fix: Address code quality and security issues"
  ```

**Success Criteria**:
- [ ] Ruff linting passes with zero errors
- [ ] Ruff formatting passes
- [ ] Bandit security scan clean
- [ ] No f-strings in logger calls
- [ ] All exception logging uses `redact_for_logging()`
- [ ] No new security vulnerabilities introduced

**Reference**: Spec lines 881-884 (quality checks)

---

### Step 7: Documentation Updates

**Goal**: Update roadmap and phase plans with completion status

#### Update Phase Plans

- [ ] Mark Phase 1 as complete in PHASE_1_plan.md
  - [ ] Update status to "✅ DONE"
  - [ ] Fill in actual time spent
  - [ ] Add completion date
  - [ ] Verify all checkboxes marked

- [ ] Update this plan (PHASE_2_plan.md) as work progresses
  - [ ] Mark completed steps with ✅
  - [ ] Document any issues encountered and resolutions

#### Update Roadmap

- [ ] Update ROADMAP.md phase overview table
  - [ ] Mark Phase 1 status as "✅ DONE"
  - [ ] Add actual time for Phase 1
  - [ ] Update "Current Phase" section
  - [ ] Update Phase 2 status as work progresses

- [ ] Add history entry to ROADMAP.md
  ```markdown
  | 2025-11-16 | Phase 1 completed | Wrapper implementation & integration, 8 type: ignore removed |
  | 2025-11-16 | Phase 2 completed | Type checking verified, all quality gates passed |
  ```

- [ ] Commit documentation updates
  ```bash
  git add docs/development/garth-wrappers/
  git commit -m "docs: Update roadmap with phase completion status"
  ```

**Success Criteria**:
- [ ] Phase 1 plan marked complete
- [ ] Phase 2 plan marked complete
- [ ] Roadmap updated with actual times
- [ ] History table updated
- [ ] All documentation reflects final state

**Reference**: ROADMAP.md History section (lines 401-411 in similar docs)

---

### Step 8: Final Verification & PR Preparation

**Goal**: Comprehensive final checks before PR submission

#### Final Checklist

- [ ] All Phase 1 deliverables verified
  - [ ] Wrapper module exists with all functions
  - [ ] Unit tests exist with 90%+ coverage
  - [ ] Integration points updated (8 locations)
  - [ ] Type: ignore comments removed (8 total)

- [ ] All Phase 2 quality gates passed
  - [ ] Mypy strict mode passes on wrapper
  - [ ] Mypy passes on integration files
  - [ ] Zero Garth-related type: ignore
  - [ ] All tests passing (unit, integration, e2e)
  - [ ] Coverage thresholds met (90%+ wrapper, 80%+ overall)
  - [ ] Code quality checks clean (ruff, bandit)
  - [ ] PII redaction verified

- [ ] Documentation complete
  - [ ] Both phase plans marked complete
  - [ ] Roadmap updated
  - [ ] History recorded

#### Verification Commands Summary

Run all verification commands as final check:

```bash
# Type checking
uv --directory backend run mypy backend/app/services/garth_wrapper.py --strict
uv --directory backend run mypy backend/app/services/garmin_client.py
uv --directory backend run mypy backend/app/services/garmin_service.py

# Type: ignore removal
grep -n "type: ignore" backend/app/services/garmin_client.py backend/app/services/garmin_service.py | grep -E "(garth|oauth|activities|daily_summary|health_snapshot|profile)"

# Testing
uv --directory backend run pytest tests/ -v --cov=app --cov-fail-under=80
uv --directory backend run pytest backend/tests/unit/test_garth_wrapper.py -v --cov=app.services.garth_wrapper --cov-fail-under=90

# Code quality
uv run ruff check .
uv run ruff format --check .
uv run bandit -c backend/pyproject.toml -r backend/app/ -ll
grep -n 'logger.*f"' backend/app/services/garth_wrapper.py
```

All commands should pass/return clean results.

#### Commit Final Status

- [ ] Commit phase 2 completion
  ```bash
  git add docs/development/garth-wrappers/PHASE_2_plan.md
  git commit -m "docs: Mark Phase 2 complete - testing & quality assurance"
  ```

#### Push and Create PR

- [ ] Push phase 2 branch
  ```bash
  git push -u origin [current-branch]-phase-2
  ```

- [ ] Create PR into current branch
  ```bash
  gh pr create --base [current-branch] \
    --title "Phase 2: Testing & Quality Assurance" \
    --body "Comprehensive verification of type safety improvements:

  - Mypy passes with --strict on wrapper module
  - Mypy passes on garmin_client.py and garmin_service.py
  - Zero Garth-related type: ignore comments
  - 90%+ coverage on wrapper module
  - 80%+ overall coverage maintained
  - All code quality checks passing (ruff, bandit)
  - All tests passing (unit, integration, e2e)
  - PII redaction verified

  Ready for merge into feature branch."
  ```

**Success Criteria**:
- [ ] All verification commands pass
- [ ] Documentation complete and accurate
- [ ] Branch pushed to origin
- [ ] PR created with detailed description
- [ ] Ready for review and merge

---

## Success Criteria

### Technical Success

- [ ] Mypy strict mode passes on `garth_wrapper.py`
- [ ] Mypy passes on `garmin_client.py`
- [ ] Mypy passes on `garmin_service.py`
- [ ] Zero Garth-related `type: ignore` comments found
- [ ] All tests passing (unit, integration, e2e)
- [ ] Coverage ≥90% on wrapper module
- [ ] Coverage ≥80% overall maintained

### Quality Metrics

- [ ] Ruff linting passes
- [ ] Ruff formatting passes
- [ ] Bandit security scan clean
- [ ] No f-strings in logger calls
- [ ] All exception logging uses `redact_for_logging()`
- [ ] All imports at top of files
- [ ] Complete docstrings on all functions

### Documentation

- [ ] Phase 1 plan marked complete
- [ ] Phase 2 plan marked complete
- [ ] Roadmap updated with completion status
- [ ] History table updated
- [ ] Actual times recorded

### Project Goals Achieved

- [ ] **Type Safety**: All 8 `type: ignore` comments eliminated
- [ ] **Runtime Validation**: Pydantic models validate all Garth responses
- [ ] **Maintainability**: Clear type signatures document API structure
- [ ] **Security**: PII redaction enforced in all logging
- [ ] **Quality**: 90%+ coverage on security-critical wrapper module

---

## Notes

**Type Checking Strategy**:
- Wrapper module uses `--strict` mode (highest standard)
- Integration files use standard mypy (pragmatic approach)
- Return type `dict[str, Any]` acceptable (validated at runtime)

**Common Mypy Issues**:
- Missing return type annotations → Add explicit `-> dict[str, Any]`
- Untyped parameters → Add type hints `token: dict[str, Any]`
- Implicit Any → Make explicit with `dict[str, Any]`

**Coverage Targets**:
- Wrapper module: 90%+ (security-critical validation logic)
- Overall codebase: 80%+ (project standard)
- E2E tests: Unchanged (internal refactoring only)

**Quality Standards**:
- Ruff: Zero errors (enforced by CI)
- Bandit: Zero vulnerabilities (ll = low confidence, low severity minimum)
- PII redaction: `redact_for_logging()` for all exception logs
- No f-strings in logger calls (enforced by pre-commit hooks)

**Verification Evidence**:
Collect output from all verification commands for PR description:
- Mypy outputs (all passing)
- Grep results (zero Garth type: ignore)
- Coverage reports (90%+ wrapper, 80%+ overall)
- Code quality reports (ruff, bandit clean)

---

## Dependencies for Final PR

Final PR to main requires:
- [ ] Both Phase 1 and Phase 2 complete
- [ ] All quality gates passed
- [ ] Documentation updated
- [ ] No failing tests anywhere
- [ ] Type safety improvements verified
- [ ] Security compliance confirmed

Final PR will include:
- Summary of type safety improvements
- List of all 8 type: ignore removals
- Coverage metrics
- Quality check results
- Link to specification and roadmap
