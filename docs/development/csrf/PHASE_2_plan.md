# Phase 2: Garmin Routes CSRF Protection

**Branch**: `feat/csrf-phase-2`
**Status**: 📅 PLANNED
**Estimated Time**: 1.5 hours
**Started**: [Date to be filled]
**Completed**: [Date to be filled]

---

## Goal

Protect Garmin integration endpoints with CSRF tokens, eliminating the HIGH-RISK account linking vulnerability. This phase secures `/garmin/link` and `/garmin/sync` POST endpoints with comprehensive TDD coverage.

**Key Deliverables**:
- Protected /garmin/link endpoint (HIGH PRIORITY - account linking vulnerability)
- Protected /garmin/sync endpoint
- CSRF tokens in Garmin link form
- Token rotation on Garmin link errors
- Integration tests for Garmin CSRF protection

**Security Impact**:
- **CRITICAL**: Blocks Garmin account linking attack (attacker cannot link their account to victim's profile)
- Prevents unwanted data sync operations
- Completes CSRF protection across all POST endpoints in Selflytics

---

## Prerequisites

**Required Before Starting**:
- [x] Phase 1 completed and merged into feat/csrf branch
- [x] Current branch: `feat/csrf` (up to date with Phase 1)
- [x] CSRF protection infrastructure working (verified in Phase 1)
- [x] All Phase 1 tests passing

**Specification Context**:
- Lines 102-168: Garmin Account Linking Attack scenario (HIGH SEVERITY)
- Lines 369-404: Route protection pattern (same as auth routes)
- Lines 409-449: Template integration pattern
- Lines 654-729: Journey 2 - CSRF Attack Blocked (Garmin Link)

---

## Deliverables

### Modified Files
- [ ] `backend/app/routes/garmin.py` - Protect POST routes, update GET route
- [ ] `backend/app/templates/fragments/garmin_link_form.html` - Add csrf_token hidden field

### New Tests
- [ ] `backend/tests/integration/test_csrf_routes.py` - Add Garmin route tests (extend existing file)

---

## Implementation Steps

### Setup

- [ ] ⏳ NEXT: Create branch from feat/csrf
  ```bash
  git checkout feat/csrf
  git pull origin feat/csrf  # Ensure Phase 1 merged
  git checkout -b feat/csrf-phase-2
  ```

---

### Step 1: Protect /garmin/link Endpoint (HIGH PRIORITY)

**Goal**: Add CSRF protection to Garmin account linking (highest risk endpoint)

**File**: `backend/app/routes/garmin.py`

#### Integration Tests (TDD)

- [ ] Write tests in `backend/tests/integration/test_csrf_routes.py` (append to existing file)
  ```python
  def test_garmin_link_requires_csrf_token(authenticated_client: TestClient):
      """Test that /garmin/link rejects requests without CSRF token."""
      response = authenticated_client.post(
          "/garmin/link",
          data={
              "username": "test@garmin.com",
              "password": "GarminPass123",
              # csrf_token intentionally omitted
          },
      )

      assert response.status_code == 403
      assert "CSRF" in response.text or "Security validation" in response.text


  def test_garmin_link_with_valid_csrf_token(authenticated_client: TestClient):
      """Test that /garmin/link accepts valid CSRF token."""
      # Get form with CSRF token
      form_response = authenticated_client.get("/garmin/link")
      assert form_response.status_code == 200

      # Extract CSRF token
      csrf_cookie = form_response.cookies.get("csrf_token")
      assert csrf_cookie is not None

      soup = BeautifulSoup(form_response.text, "html.parser")
      csrf_input = soup.find("input", {"name": "csrf_token"})
      assert csrf_input is not None
      csrf_token = csrf_input["value"]

      # Submit with valid token (may fail auth, but not CSRF)
      response = authenticated_client.post(
          "/garmin/link",
          data={
              "username": "test@garmin.com",
              "password": "WrongGarminPass",
              "csrf_token": csrf_token,
          },
          cookies={"csrf_token": csrf_cookie},
      )

      # Should fail Garmin auth (400), not CSRF (403)
      assert response.status_code in (200, 400, 500)
      assert response.status_code != 403  # Not CSRF error


  def test_csrf_token_rotation_on_garmin_link_error(authenticated_client: TestClient):
      """Test that CSRF token is rotated when Garmin link fails."""
      # Get initial form
      form1 = authenticated_client.get("/garmin/link")
      token1 = form1.cookies.get("csrf_token")
      soup1 = BeautifulSoup(form1.text, "html.parser")
      csrf_token1 = soup1.find("input", {"name": "csrf_token"})["value"]

      # Submit with wrong credentials (will fail)
      response = authenticated_client.post(
          "/garmin/link",
          data={
              "username": "test@garmin.com",
              "password": "WrongPassword",
              "csrf_token": csrf_token1,
          },
          cookies={"csrf_token": token1},
          headers={"HX-Request": "true"},
      )

      assert response.status_code in (400, 500)

      # Token should be rotated
      token2 = response.cookies.get("csrf_token")
      assert token2 is not None
      assert token2 != token1

      # Extract new token from form
      soup2 = BeautifulSoup(response.text, "html.parser")
      csrf_input2 = soup2.find("input", {"name": "csrf_token"})
      assert csrf_input2 is not None
      csrf_token2 = csrf_input2["value"]
      assert csrf_token2 != csrf_token1
  ```

- [ ] Run tests, verify they fail
  ```bash
  uv --directory backend run pytest tests/integration/test_csrf_routes.py::test_garmin_link_requires_csrf_token -v
  ```

#### Implementation

- [ ] Add import at top of garmin.py
  ```python
  from fastapi_csrf_protect import CsrfProtect
  ```

- [ ] Update GET /garmin/link endpoint to generate CSRF token
  ```python
  @router.get("/link", response_class=HTMLResponse)
  async def garmin_link_page(
      request: Request,
      current_user: UserResponse = Depends(get_current_user),
      csrf_protect: CsrfProtect = Depends(),  # Add CSRF dependency
      templates=Depends(get_templates),
  ):
      """Display Garmin account linking form with CSRF token."""
      csrf_token, signed_token = csrf_protect.generate_csrf_tokens()
      response = templates.TemplateResponse(
          request=request,
          name="settings_garmin.html",
          context={
              "user": current_user,
              "csrf_token": csrf_token,  # Pass to template
          },
      )
      csrf_protect.set_csrf_cookie(signed_token, response)
      return response
  ```

- [ ] Update POST /garmin/link endpoint to validate CSRF token
  ```python
  @router.post("/link", response_class=HTMLResponse)
  async def link_garmin_account(
      request: Request,
      csrf_protect: CsrfProtect = Depends(),  # Add CSRF dependency
      username: str = Form(...),
      password: str = Form(...),
      current_user: UserResponse = Depends(get_current_user),
      templates=Depends(get_templates),
  ):
      """Link Garmin account to user."""

      # Validate CSRF token FIRST
      await csrf_protect.validate_csrf(request)

      try:
          service = GarminService(current_user.user_id)

          success = await service.link_account(
              username=username,
              password=password,
          )

          if not success:
              # Generate NEW token for form re-render
              csrf_token, signed_token = csrf_protect.generate_csrf_tokens()
              response = templates.TemplateResponse(
                  request=request,
                  name="fragments/garmin_link_form.html",
                  context={
                      "csrf_token": csrf_token,  # NEW token
                      "error_message": "Please check your credentials and try again.",
                  },
                  status_code=400,
              )
              csrf_protect.set_csrf_cookie(signed_token, response)
              return response

          # Success - return linked status view (no form, no token needed)
          return templates.TemplateResponse(
              request=request,
              name="fragments/garmin_linked_success.html",
              status_code=200,
          )
      except HTTPException:
          raise  # Re-raise expected HTTP exceptions
      except Exception as e:
          # Log detailed error (with redaction) for debugging
          logger.error(
              "Garmin link failed for user %s: %s",
              current_user.user_id,
              redact_for_logging(str(e)),
          )

          # Generate NEW token for form re-render
          csrf_token, signed_token = csrf_protect.generate_csrf_tokens()
          response = templates.TemplateResponse(
              request=request,
              name="fragments/garmin_link_form.html",
              context={
                  "csrf_token": csrf_token,  # NEW token
                  "error_title": "Something went wrong",
                  "error_message": "An unexpected error occurred. Please try again later.",
              },
              status_code=500,
          )
          csrf_protect.set_csrf_cookie(signed_token, response)
          return response
  ```

- [ ] Run integration tests, verify they pass
  ```bash
  uv --directory backend run pytest tests/integration/test_csrf_routes.py -v -k garmin_link
  ```

- [ ] Commit Garmin link protection
  ```bash
  git add backend/app/routes/garmin.py backend/tests/integration/test_csrf_routes.py
  git commit -m "feat: Add CSRF protection to /garmin/link endpoint (HIGH PRIORITY)"
  ```

**Success Criteria**:
- [ ] GET /garmin/link generates and sets CSRF token
- [ ] POST /garmin/link validates CSRF token
- [ ] Token rotation works on link failure
- [ ] Token rotation works on exceptions
- [ ] Integration tests pass

**Reference**: Spec lines 102-168 (attack scenario), 369-404 (protection pattern)

---

### Step 2: Update Garmin Link Form Template

**Goal**: Add hidden csrf_token field to Garmin link form

**File**: `backend/app/templates/fragments/garmin_link_form.html`

#### Implementation

- [ ] Add csrf_token hidden field as FIRST field in form (after opening `<form>` tag, before line 11)
  ```html
  <form
      data-testid="form-link-garmin"
      hx-post="/garmin/link"
      hx-swap="outerHTML"
      x-data="{ loading: false }"
      @submit="loading = true"
      data-reset-loading-on-swap
      class="bg-white border border-gray-200 rounded-lg p-6 shadow-sm space-y-4"
  >
      <!-- CSRF Token (MUST be first field) -->
      <input type="hidden" name="csrf_token" value="{{ csrf_token }}">

      {% if error_message %}
      <!-- Error message -->
      ...
  ```

- [ ] Verify template renders correctly
  ```bash
  # Start dev server
  ./scripts/dev-server.sh
  # Login, visit http://localhost:8000/garmin/link
  # Inspect HTML, verify hidden csrf_token field exists
  ```

- [ ] Commit template update
  ```bash
  git add backend/app/templates/fragments/garmin_link_form.html
  git commit -m "feat: Add CSRF token to Garmin link form template"
  ```

**Success Criteria**:
- [ ] Hidden input field with name="csrf_token" exists
- [ ] Field is first in form
- [ ] Value populated from template context

**Reference**: Spec lines 432-449

---

### Step 3: Protect /garmin/sync Endpoint

**Goal**: Add CSRF protection to Garmin data sync endpoint

**File**: `backend/app/routes/garmin.py`

#### Integration Tests (TDD)

- [ ] Write tests in `backend/tests/integration/test_csrf_routes.py`
  ```python
  def test_garmin_sync_requires_csrf_token(authenticated_client: TestClient):
      """Test that /garmin/sync rejects requests without CSRF token."""
      response = authenticated_client.post(
          "/garmin/sync",
          data={
              # csrf_token intentionally omitted
          },
      )

      assert response.status_code == 403
      assert "CSRF" in response.text or "Security validation" in response.text


  def test_garmin_sync_with_valid_csrf_token(authenticated_client: TestClient):
      """Test that /garmin/sync accepts valid CSRF token.

      Note: This test may fail with 400 (no linked account) but should not fail with 403 (CSRF).
      """
      # Note: In real implementation, we'd need to link Garmin account first
      # For now, just verify CSRF validation happens before business logic

      # Get a CSRF token (from link page or dashboard)
      form_response = authenticated_client.get("/garmin/link")
      csrf_cookie = form_response.cookies.get("csrf_token")
      soup = BeautifulSoup(form_response.text, "html.parser")
      csrf_token = soup.find("input", {"name": "csrf_token"})["value"]

      # Submit sync with valid CSRF token
      response = authenticated_client.post(
          "/garmin/sync",
          data={
              "csrf_token": csrf_token,
          },
          cookies={"csrf_token": csrf_cookie},
      )

      # Should fail business logic (400/500), not CSRF (403)
      assert response.status_code in (200, 400, 500)
      assert response.status_code != 403
  ```

- [ ] Run tests, verify they fail
  ```bash
  uv --directory backend run pytest tests/integration/test_csrf_routes.py::test_garmin_sync_requires_csrf_token -v
  ```

#### Implementation

- [ ] Update POST /garmin/sync endpoint to validate CSRF token (around line 95+)
  ```python
  @router.post("/sync", response_class=HTMLResponse)
  async def sync_garmin_data(
      request: Request,
      csrf_protect: CsrfProtect = Depends(),  # Add CSRF dependency
      current_user: UserResponse = Depends(get_current_user),
      templates=Depends(get_templates),
  ):
      """Sync Garmin data for authenticated user."""

      # Validate CSRF token FIRST
      await csrf_protect.validate_csrf(request)

      try:
          service = GarminService(current_user.user_id)
          activities = await service.sync_recent_activities()

          # Success - return success fragment
          return templates.TemplateResponse(
              request=request,
              name="fragments/garmin_sync_success.html",
              context={"activity_count": len(activities)},
              status_code=200,
          )
      except ValueError as e:
          # No Garmin account linked - return error fragment with NEW token
          csrf_token, signed_token = csrf_protect.generate_csrf_tokens()
          response = templates.TemplateResponse(
              request=request,
              name="fragments/garmin_sync_error.html",
              context={
                  "csrf_token": csrf_token,  # NEW token (if error fragment has form)
                  "error_message": str(e),
              },
              status_code=400,
          )
          csrf_protect.set_csrf_cookie(signed_token, response)
          return response
      except Exception as e:
          # Unexpected error - return error fragment with NEW token
          logger.error(
              "Garmin sync failed for user %s: %s",
              current_user.user_id,
              redact_for_logging(str(e)),
          )

          csrf_token, signed_token = csrf_protect.generate_csrf_tokens()
          response = templates.TemplateResponse(
              request=request,
              name="fragments/garmin_sync_error.html",
              context={
                  "csrf_token": csrf_token,  # NEW token
                  "error_message": "Failed to sync Garmin data. Please try again later.",
              },
              status_code=500,
          )
          csrf_protect.set_csrf_cookie(signed_token, response)
          return response
  ```

- [ ] Run integration tests, verify they pass
  ```bash
  uv --directory backend run pytest tests/integration/test_csrf_routes.py -v -k garmin_sync
  ```

- [ ] Commit Garmin sync protection
  ```bash
  git add backend/app/routes/garmin.py backend/tests/integration/test_csrf_routes.py
  git commit -m "feat: Add CSRF protection to /garmin/sync endpoint"
  ```

**Success Criteria**:
- [ ] POST /garmin/sync validates CSRF token
- [ ] Token rotation works on errors
- [ ] Integration tests pass

**Reference**: Spec lines 369-404 (protection pattern)

**Note**: If garmin_sync_error.html or garmin_sync_success.html fragments contain forms that can retry, they'll need csrf_token fields. Based on existing templates, sync success likely doesn't have a form, but sync error might.

---

### Test Verification

**Goal**: Verify all Phase 2 tests pass with good coverage

- [ ] Run all integration tests
  ```bash
  uv --directory backend run pytest tests/integration -v
  ```

- [ ] Run tests with coverage report
  ```bash
  uv --directory backend run pytest tests/ -v --cov=app --cov-report=term-missing
  ```

- [ ] Verify coverage ≥ 80% on Garmin routes
  ```bash
  # Check coverage report for:
  # - app/routes/garmin.py (CSRF validation in both endpoints)
  ```

**Success Criteria**:
- [ ] All integration tests passing
- [ ] Coverage ≥ 80% on Garmin CSRF protection
- [ ] No test failures anywhere in codebase

---

### Code Quality Checks

**Goal**: Ensure code meets project quality standards

- [ ] Run linter
  ```bash
  uv run ruff check .
  ```

- [ ] Fix any linting issues
  ```bash
  uv run ruff check --fix .
  ```

- [ ] Run formatter
  ```bash
  uv run ruff format .
  ```

- [ ] Run security scanner
  ```bash
  uv run bandit -c backend/pyproject.toml -r backend/app/ -ll
  ```

**Success Criteria**:
- [ ] No ruff errors
- [ ] Code formatted consistently
- [ ] No security warnings from bandit

---

### Manual Verification

**Goal**: Manually verify Garmin CSRF protection works

- [ ] Start development server
  ```bash
  ./scripts/dev-server.sh
  ```

- [ ] Test Garmin link flow
  - [ ] Login to Selflytics
  - [ ] Navigate to http://localhost:8000/garmin/link
  - [ ] Open DevTools → Elements
  - [ ] Verify `<input type="hidden" name="csrf_token">` exists
  - [ ] Verify value is non-empty (32+ characters)
  - [ ] Open DevTools → Application → Cookies
  - [ ] Verify `csrf_token` cookie exists
  - [ ] Submit with wrong Garmin credentials
  - [ ] Verify form re-renders with error
  - [ ] Verify NEW csrf_token value (token rotated)

- [ ] Test CSRF attack prevention (HIGH PRIORITY)
  - [ ] Create malicious HTML file (from spec lines 112-123)
    ```html
    <!DOCTYPE html>
    <html>
    <body onload="document.forms[0].submit()">
      <form action="http://localhost:8000/garmin/link" method="POST">
        <input type="hidden" name="username" value="attacker@evil.com">
        <input type="hidden" name="password" value="attacker-password">
      </form>
    </body>
    </html>
    ```
  - [ ] While logged into Selflytics, open this HTML file in browser
  - [ ] Verify attack is BLOCKED (403 error or no action)
  - [ ] Verify Garmin account NOT linked to attacker's credentials

**Success Criteria**:
- [ ] CSRF tokens visible in Garmin form
- [ ] Token rotation works on link errors
- [ ] **CRITICAL**: Garmin link attack BLOCKED
- [ ] Legitimate Garmin link requests succeed (with valid credentials)

**Reference**: Spec lines 1160-1200 (manual testing)

---

### Git Workflow

**Goal**: Push branch and create PR into feat/csrf

- [ ] Final commit with phase completion
  ```bash
  git add .
  git commit -m "docs: Mark Phase 2 complete in plan"
  ```

- [ ] Push phase branch
  ```bash
  git push -u origin feat/csrf-phase-2
  ```

- [ ] Create PR into feat/csrf
  ```bash
  gh pr create --base feat/csrf --title "Phase 2: Garmin Routes CSRF Protection" \
    --body "Implements CSRF protection for Garmin integration endpoints, eliminating HIGH-RISK account linking vulnerability.

  **Changes**:
  - Protect /garmin/link endpoint (HIGH PRIORITY)
  - Protect /garmin/sync endpoint
  - Add CSRF token to Garmin link form
  - Token rotation on Garmin errors

  **Testing**:
  - Integration tests for Garmin routes
  - Coverage: XX% (≥80% target)
  - Manual testing: Attack prevention verified

  **Security Impact**:
  - BLOCKS Garmin account linking attack (Spec lines 102-168)
  - Prevents unwanted data sync operations

  **Part of**: #8"
  ```

- [ ] Update this plan: Mark all steps ✅ DONE
- [ ] Update ROADMAP.md: Phase 2 status → ✅ DONE

**Success Criteria**:
- [ ] PR created targeting feat/csrf branch
- [ ] PR description clear and complete
- [ ] CI checks passing on PR
- [ ] Phase 2 plan marked complete

---

## Success Criteria

### Technical Success

- [x] /garmin/link requires valid CSRF token (HIGH PRIORITY)
- [x] /garmin/sync requires valid CSRF token
- [x] Garmin link form includes hidden csrf_token field
- [x] Token rotation works on Garmin link errors
- [x] Integration tests pass (Garmin routes protected)

### Security Success

- [x] **CRITICAL**: Garmin account linking attack BLOCKED
- [x] Cross-origin POST to /garmin/link rejected with 403
- [x] Attacker cannot link their account to victim's profile
- [x] Manual attack simulation fails (verified)

### Quality Metrics

- [x] 80%+ test coverage on Garmin CSRF protection
- [x] All quality gates pass (ruff, bandit)
- [x] No regressions in existing tests

---

## Notes

### Design Decisions

- **Token rotation on ALL Garmin errors**: Both link failures and sync failures rotate tokens
- **Consistent error handling**: Same pattern as auth routes (generic messages, new tokens)
- **High priority on /garmin/link**: This endpoint has highest security risk (account linking attack)

### Specification References

- Lines 102-168: Garmin Account Linking Attack scenario (HIGH SEVERITY)
- Lines 369-404: Route protection pattern
- Lines 654-729: Journey 2 - CSRF Attack Blocked (Garmin Link)

### Attack Scenario Prevented

From specification (lines 102-168):

**Before CSRF Protection**:
1. Victim logs into Selflytics → has valid access_token cookie
2. Victim visits attacker's malicious website
3. Malicious site auto-submits form to /garmin/link with attacker's credentials
4. Browser sends victim's access_token cookie automatically
5. Backend links attacker's Garmin account to victim's Selflytics profile
6. Victim sees attacker's fitness data instead of their own

**After CSRF Protection**:
1. Victim logs into Selflytics → has valid access_token cookie
2. Victim visits attacker's malicious website
3. Malicious site auto-submits form to /garmin/link with attacker's credentials
4. Browser sends victim's access_token cookie automatically
5. ✅ **Backend rejects request (403) - NO CSRF TOKEN**
6. ✅ **Victim's account remains secure**

---

## Dependencies for Next Phase

**Phase 3 needs from Phase 2**:
- [x] All POST endpoints protected (/auth/register, /auth/login, /garmin/link, /garmin/sync)
- [x] Token rotation working across all routes
- [x] Integration tests passing
- [x] Manual verification that attack prevention works

---

## Session Notes

### Session 2 (2025-11-15): PR Feedback Implementation + E2E Test Fix

**Context**: Addressed PR #17 review feedback and resolved critical e2e test infrastructure issue.

#### PR #17 Feedback Implementation

**Changes Made**:
1. Added CSRF token rotation to sync error exception handler (`garmin.py:143-151`)
2. Added CSRF protection to DELETE /garmin/link endpoint (`garmin.py:154-162`)
3. Created comprehensive tests in `test_csrf_routes.py`:
   - `test_csrf_token_rotation_on_garmin_sync_error` - verifies token rotation on sync failures
   - `test_garmin_unlink_requires_csrf_token` - verifies DELETE endpoint requires token
   - `test_garmin_unlink_with_valid_csrf_token` - verifies DELETE accepts valid tokens
4. Fixed broken unit tests in `test_template_data_testids.py` (needed CSRF tokens after protection added)

**Commits**:
- `feat: Add CSRF token rotation to sync error handler`
- `test: Add CSRF protection tests for sync error and DELETE endpoint`
- `fix: Update template testid tests to include CSRF tokens`

#### Critical E2E Test Infrastructure Fix

**Problem**: All 29 e2e tests hung indefinitely during Playwright browser initialization, timing out after 60 seconds.

**Root Cause** (found by debug-investigator agent):
- **Event loop scope mismatch** between pytest-asyncio and pytest-playwright-asyncio
- pytest-playwright-asyncio provides **session-scoped** async fixtures (browser, page)
- Test functions defaulted to **function-scoped** event loops (missing config)
- Mismatched scopes caused deadlock when tests tried to use session fixtures

**Solution**: Added one line to `backend/pyproject.toml`:
```toml
asyncio_default_test_loop_scope = "session"
```

**Results**:
- **Before**: 366 tests (e2e excluded), tests hung for 60+ seconds
- **After**: 401 tests total, 390 passed + 11 skipped, 92% coverage, **54.61 seconds**
- E2E tests now run in default test suite (removed `--ignore=tests/e2e_playwright`)

**Additional Infrastructure Improvements**:
- Added `pytest-timeout>=2.3.1` with 30s default to catch hung tests early
- Improved `scripts/local-e2e-server.sh` to kill existing processes before starting
- Verified Playwright browsers installed correctly in macOS cache location

**Commits**:
- `fix: Configure session-scoped event loop for e2e tests`
- `chore: Re-enable e2e tests in default test runs`
- `chore: Update dependencies and improve local e2e server script`
- `chore: Add pytest-timeout to workspace dev dependencies`

**Test Verification**:
```bash
# Full test suite with e2e
uv --directory backend run pytest tests/ --cov=app
# Result: 390 passed, 11 skipped, 92% coverage in 54.61s

# E2E tests isolated
uv --directory backend run pytest tests/e2e_playwright/ -v
# Result: 29 passed in 29.21s
```

**Impact**:
- ✅ Complete test coverage now includes 29 e2e browser tests
- ✅ Tests run fast and reliably (no more timeouts)
- ✅ E2E infrastructure ready for CI/CD integration
- ✅ Local development workflow improved (automatic cleanup of stale processes)

**Key Learning**: Playwright async fixtures require matching test loop scope. The debug-investigator agent systematically ruled out browser installation, server connectivity, and zombie processes before identifying the pytest configuration mismatch as the root cause.

---

*Last Updated: 2025-11-15*
*Status: ✅ COMPLETE (PR #17 feedback addressed, e2e tests fixed)*
