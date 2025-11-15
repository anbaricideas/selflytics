# Phase 3: Documentation & Validation

**Branch**: `chore/csrf-improvements-phase-3`
**Status**: NOT STARTED
**Estimated Time**: 0.5 hours

---

## Goal

Update documentation to reflect new CSRF protections, run comprehensive validation checks, and prepare for final PR to main branch.

---

## Prerequisites

- [ ] Phase 1 completed (logout protection)
- [ ] Phase 2 completed (chat send protection)
- [ ] All tests passing in both phases
- [ ] Current branch is `chore/csrf-improvements`

---

## Deliverables

### Documentation Updates
- Updated parent CSRF specification with new protected endpoints
- Updated endpoint coverage table

### Validation
- Full test suite verification (unit, integration, E2E)
- Test coverage report (≥80%)
- Security scan clean
- Type checking clean
- Linting clean

### Preparation
- Phase plans marked complete
- Roadmap updated with actual hours
- Final cleanup commits

---

## Implementation Steps

### Setup

- [ ] ⏳ NEXT: Create branch from `chore/csrf-improvements`
  ```bash
  git checkout chore/csrf-improvements
  git pull origin chore/csrf-improvements
  git checkout -b chore/csrf-improvements-phase-3
  ```

---

### Step 1: Update Parent CSRF Specification

**File**: `/Users/bryn/repos/selflytics/docs/development/csrf/CSRF_SPECIFICATION.md`

**Reference**: Specification (improvements spec) lines 1045-1067

#### Add new endpoints to protected endpoints list

- [ ] Open `/Users/bryn/repos/selflytics/docs/development/csrf/CSRF_SPECIFICATION.md`
- [ ] Locate the "Current Attack Surface" or "Protected Endpoints" section
- [ ] Add documentation for newly protected endpoints:

  ```markdown
  ### Protected Endpoints (Updated 2025-11-16)

  #### Authentication Routes
  - `/auth/register` - CSRF protected (form-based)
  - `/auth/login` - CSRF protected (form-based)
  - `/logout` - CSRF protected (form-based) - **Added in CSRF improvements**

  #### Garmin Integration Routes
  - `/garmin/link` - CSRF protected (form-based)
  - `/garmin/sync` - CSRF protected (form-based)
  - `DELETE /garmin/link` - CSRF protected (header-based)

  #### Chat Routes
  - `POST /chat/send` - CSRF protected (header-based) - **Added in CSRF improvements**

  ### Protection Patterns

  #### Form-Based Protection
  Used for traditional HTML form submissions:
  - Token in hidden input field: `<input type="hidden" name="fastapi-csrf-token" value="{{ csrf_token }}">`
  - Token in cookie: `fastapi-csrf-token`
  - Validation: Server compares form field value with signed cookie value

  **Endpoints**: `/auth/register`, `/auth/login`, `/logout`, `/garmin/link`, `/garmin/sync`

  #### Header-Based Protection
  Used for JSON API requests and JavaScript-initiated requests:
  - Token in HTTP header: `X-CSRF-Token: <token>`
  - Token in cookie: `fastapi-csrf-token`
  - JavaScript reads token from cookie (requires `httponly=false`)
  - Validation: Server compares header value with cookie value

  **Endpoints**: `DELETE /garmin/link`, `POST /chat/send`

  ### Related Documentation

  - **CSRF Improvements Specification**: `/Users/bryn/repos/selflytics/docs/development/csrf-improvements/SPECIFICATION.md`
  - **Issue #12**: Integrate CSRF protection into settings page logout form
  ```

- [ ] Save file

#### Commit

- [ ] Commit documentation updates
  ```bash
  git add docs/development/csrf/CSRF_SPECIFICATION.md
  git commit -m "docs: Update CSRF spec with logout and chat send protections

- Add /logout to protected endpoints (form-based)
- Add POST /chat/send to protected endpoints (header-based)
- Document form-based vs header-based protection patterns
- Reference CSRF improvements spec and issue #12"
  ```

---

### Step 2: Run Comprehensive Test Suite

**Goal**: Verify all tests pass across all test types

#### Run all tests with coverage

- [ ] Run full test suite
  ```bash
  uv --directory backend run pytest tests/ -v --cov=app --cov-report=term-missing
  ```
- [ ] Verify results:
  - All tests pass (0 failures, 0 errors)
  - Coverage ≥ 80%
  - No missing coverage in critical paths

#### Run tests by category

- [ ] Run unit tests
  ```bash
  uv --directory backend run pytest tests/unit -v
  ```
- [ ] Verify: All unit tests pass

- [ ] Run integration tests
  ```bash
  uv --directory backend run pytest tests/integration -v
  ```
- [ ] Verify: All integration tests pass

- [ ] Run E2E tests (requires local-e2e-server.sh)
  ```bash
  ./scripts/local-e2e-server.sh  # Start in separate terminal
  uv --directory backend run pytest tests/e2e_playwright -v
  ```
- [ ] Verify: All E2E tests pass
- [ ] Stop local-e2e-server.sh

#### Document test results

- [ ] Record test summary:
  - Total tests: ___
  - Passed: ___
  - Failed: ___
  - Coverage: ____%

**If any tests fail**: Debug and fix before proceeding. This is the final validation gate.

---

### Step 3: Run Code Quality Checks

**Goal**: Ensure code meets all quality standards

#### Type Checking

- [ ] Run mypy on entire app
  ```bash
  uv run mypy backend/app
  ```
- [ ] Verify: No type errors
- [ ] If errors found, fix them and commit:
  ```bash
  git add <fixed-files>
  git commit -m "fix: Resolve mypy type errors"
  ```

#### Linting

- [ ] Run ruff check
  ```bash
  uv run ruff check .
  ```
- [ ] Verify: No linting errors
- [ ] If errors found, auto-fix:
  ```bash
  uv run ruff check . --fix
  git add -A
  git commit -m "chore: Fix linting errors (ruff)"
  ```

#### Formatting

- [ ] Run ruff format
  ```bash
  uv run ruff format .
  ```
- [ ] If formatting changes made, commit:
  ```bash
  git add -A
  git commit -m "chore: Apply code formatting (ruff)"
  ```

---

### Step 4: Run Security Scan

**Goal**: Ensure no security vulnerabilities introduced

- [ ] Run bandit security scanner
  ```bash
  uv run bandit -c backend/pyproject.toml -r backend/app/ -ll
  ```
- [ ] Verify: No security warnings
- [ ] Check for CSRF-related patterns:
  - No hardcoded tokens
  - No insecure cookie settings
  - Proper exception handling

**If security warnings found**: Review and fix. Security issues are blockers.

---

### Step 5: Update Phase Plans and Roadmap

**Goal**: Mark work complete and record actual hours

#### Update Phase 1 Plan

- [ ] Open `/Users/bryn/repos/selflytics/docs/development/csrf-improvements/PHASE_1_plan.md`
- [ ] Verify all checkboxes are marked complete
- [ ] Update status at top to: `**Status**: ✅ DONE`

#### Update Phase 2 Plan

- [ ] Open `/Users/bryn/repos/selflytics/docs/development/csrf-improvements/PHASE_2_plan.md`
- [ ] Verify all checkboxes are marked complete
- [ ] Update status at top to: `**Status**: ✅ DONE`

#### Update Phase 3 Plan (this plan)

- [ ] Update status at top to: `**Status**: IN PROGRESS` (will mark DONE at end)

#### Update Roadmap

- [ ] Open `/Users/bryn/repos/selflytics/docs/development/csrf-improvements/ROADMAP.md`
- [ ] Update Phase Overview table:
  - Phase 1: Status = ✅ DONE, record actual hours
  - Phase 2: Status = ✅ DONE, record actual hours
  - Phase 3: Status = IN PROGRESS
- [ ] Calculate actual hours using git log:
  ```bash
  # From start of phase 1 to current HEAD
  git log --oneline chore/csrf-improvements..HEAD --format="%ad" --date=format:"%Y-%m-%d %H:00" | uniq | wc -l
  ```
- [ ] Update "Total Estimated Time" with actual time
- [ ] Update History table with completion dates

#### Commit

- [ ] Commit documentation updates
  ```bash
  git add docs/development/csrf-improvements/
  git commit -m "docs: Mark phases 1-2 complete and update roadmap

- Phase 1 complete: Logout endpoint protection
- Phase 2 complete: Chat send endpoint protection
- Record actual hours spent
- Update phase statuses"
  ```

---

### Step 6: Final Verification Checklist

**Goal**: Confirm all success criteria met

#### Functional Requirements

- [ ] `/logout` endpoint validates CSRF token before processing
- [ ] Settings page logout form includes CSRF token
- [ ] Chat page logout form includes CSRF token
- [ ] Logout without valid CSRF token returns 403 and preserves session
- [ ] Logout with valid CSRF token clears session and redirects to login
- [ ] `/chat/send` endpoint validates CSRF token before processing
- [ ] Chat interface JavaScript reads CSRF token from cookie
- [ ] Chat interface sends X-CSRF-Token header with requests
- [ ] Chat interface handles missing token gracefully
- [ ] Chat interface handles expired token with auto-refresh

#### Security Requirements

- [ ] Forged logout request (no token) is blocked (403)
- [ ] Forged chat request (no token) is blocked (403)
- [ ] CSRF cookie configuration verified (`httponly=false`)
- [ ] CSRF cookie uses `SameSite=strict`
- [ ] Token expiration enforced (1 hour max age)
- [ ] Generic error messages prevent user enumeration

#### Testing Requirements

- [ ] Integration tests for logout (all scenarios)
- [ ] Integration tests for chat/send (all scenarios)
- [ ] E2E test: cross-origin logout attack blocked
- [ ] E2E test: cross-origin chat attack blocked
- [ ] E2E test: legitimate logout works
- [ ] E2E test: legitimate chat message sending works
- [ ] Manual testing complete (DevTools verification)

#### Documentation Requirements

- [ ] Parent CSRF specification updated
- [ ] Logout protection documented
- [ ] Chat send protection documented
- [ ] Token expiration handling documented

---

### Step 7: Update Phase 3 Status

- [ ] Mark all checkboxes in this plan as complete
- [ ] Update status at top of document to ✅ DONE
- [ ] Commit final phase plan update:
  ```bash
  git add docs/development/csrf-improvements/PHASE_3_plan.md
  git commit -m "docs: Mark Phase 3 complete"
  ```

---

### Step 8: Final Push and PR

- [ ] Update roadmap with Phase 3 completion:
  ```bash
  # Edit ROADMAP.md: Phase 3 Status = ✅ DONE
  git add docs/development/csrf-improvements/ROADMAP.md
  git commit -m "docs: Mark all phases complete"
  ```

- [ ] Review all changes since phase start:
  ```bash
  git log --oneline chore/csrf-improvements..HEAD
  git diff chore/csrf-improvements...HEAD
  ```

- [ ] Push phase 3 branch:
  ```bash
  git push origin chore/csrf-improvements-phase-3
  ```

- [ ] Create PR to `chore/csrf-improvements` (not main)
  - Title: "Phase 3: Documentation & Validation"
  - Description: "Final validation and documentation updates"
  - Link to issue #12

- [ ] Merge phase 3 PR to `chore/csrf-improvements`

- [ ] Switch to main feature branch:
  ```bash
  git checkout chore/csrf-improvements
  git pull origin chore/csrf-improvements
  ```

- [ ] Final verification on feature branch:
  ```bash
  uv --directory backend run pytest tests/ -v
  ```

- [ ] Create final PR to `main`:
  - Title: "Close CSRF protection gaps for logout and chat endpoints"
  - Description: Reference SPECIFICATION.md and issue #12
  - Include summary of changes:
    - Protected `/logout` endpoint
    - Protected `POST /chat/send` endpoint
    - Added integration and E2E tests
    - Updated documentation
  - Request review

---

## Success Criteria

### Documentation

- [x] Parent CSRF spec updated with new endpoints
- [x] Protection patterns documented (form-based vs header-based)
- [x] Phase plans marked complete
- [x] Roadmap updated with actual hours

### Validation

- [x] All tests pass (unit, integration, E2E)
- [x] Test coverage ≥ 80%
- [x] No type errors (mypy clean)
- [x] No linting errors (ruff clean)
- [x] No security warnings (bandit clean)

### Preparation

- [x] All success criteria verified
- [x] Final PR created to main
- [x] Ready for code review

---

## Notes

### Validation Checklist

This phase serves as the final quality gate before merging to main. All checks must pass:

1. ✅ Functional requirements verified
2. ✅ Security requirements verified
3. ✅ Testing requirements verified
4. ✅ Documentation requirements verified
5. ✅ Code quality checks pass
6. ✅ Security scan clean

### Final PR Description Template

```markdown
## Summary

Closes CSRF protection gaps identified in security review (Issue #12).

## Changes

### Phase 1: Logout Protection
- Added CSRF validation to `POST /logout` endpoint
- Updated GET `/settings` and GET `/chat/` to generate CSRF tokens
- Added CSRF tokens to logout forms in settings.html and chat.html
- Integration tests for all scenarios

### Phase 2: Chat Send Protection
- Added CSRF validation to `POST /chat/send` endpoint
- Implemented header-based CSRF protection (X-CSRF-Token)
- Added JavaScript helper to read token from cookie
- Token expiration handling with auto-refresh
- Integration and E2E tests

### Phase 3: Documentation & Validation
- Updated parent CSRF specification
- Comprehensive test suite validation
- Security scan verification

## Testing

- ✅ All unit tests pass
- ✅ All integration tests pass (including 8 new tests)
- ✅ All E2E tests pass (including 3 new security tests)
- ✅ Coverage maintained at 80%+
- ✅ Manual testing verified

## Security

- ✅ Prevents forced logout attacks
- ✅ Prevents chat message injection attacks
- ✅ Prevents resource consumption abuse
- ✅ Follows existing CSRF patterns from PR #21
- ✅ Bandit security scan clean

## References

- Specification: `/Users/bryn/repos/selflytics/docs/development/csrf-improvements/SPECIFICATION.md`
- Issue: #12
- Parent spec: `/Users/bryn/repos/selflytics/docs/development/csrf/CSRF_SPECIFICATION.md`

## Review Notes

- All changes follow TDD workflow (tests written first)
- Patterns consistent with existing CSRF implementation (PR #21)
- No breaking changes to user experience
- Documentation complete
```

---

**End of Phase 3 Plan**
