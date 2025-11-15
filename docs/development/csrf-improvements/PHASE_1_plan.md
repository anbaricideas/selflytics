# Phase 1: Protect Logout Endpoint

**Branch**: `chore/csrf-improvements-phase-1`
**Status**: ⏳ NEXT
**Estimated Time**: 1.5 hours

---

## Goal

Add CSRF protection to the `/logout` endpoint and all logout forms across the application to prevent forced logout attacks. This protects users from malicious sites that could log them out without their consent.

---

## Prerequisites

- [x] CSRF infrastructure already exists (from PR #21)
- [x] Current branch is `chore/csrf-improvements`
- [x] All existing tests passing
- [x] Specification read: `/Users/bryn/repos/selflytics/docs/development/csrf-improvements/SPECIFICATION.md` (lines 189-441)

---

## Deliverables

### Backend Changes
- Updated `/logout` endpoint in `backend/app/routes/auth.py` with CSRF validation
- Updated GET `/settings` endpoint in `backend/app/routes/dashboard.py` to generate CSRF tokens
- Updated GET `/chat/` endpoint in `backend/app/routes/chat.py` to generate CSRF tokens

### Template Changes
- Updated `backend/app/templates/settings.html` logout form with CSRF token
- Updated `backend/app/templates/chat.html` logout form with CSRF token

### Tests
- Integration tests for logout CSRF protection in `backend/tests/integration/test_csrf_routes.py`
- Manual testing verification checklist

---

## Implementation Steps

### Setup

- [ ] ⏳ NEXT: Create branch from `chore/csrf-improvements`
  ```bash
  git checkout chore/csrf-improvements
  git pull origin chore/csrf-improvements
  git checkout -b chore/csrf-improvements-phase-1
  ```

---

### Step 1: Audit Logout Forms (TDD - Research)

**Goal**: Identify all logout forms in codebase to ensure complete coverage

#### Research Tasks

- [ ] Search for all logout form instances
  ```bash
  grep -rn 'action="/logout"' /Users/bryn/repos/selflytics/backend/app/templates/
  ```
- [ ] Verify expected instances found:
  - `backend/app/templates/settings.html` (line ~16)
  - `backend/app/templates/chat.html` (line ~30)
- [ ] Check for any other logout mechanisms (links, JavaScript, etc.)
  ```bash
  grep -rn '/logout' /Users/bryn/repos/selflytics/backend/app/templates/ | grep -v 'action="/logout"'
  ```
- [ ] Document findings in notes below

**Expected Findings**:
- 2 logout forms (settings.html, chat.html)
- No other logout mechanisms

**Notes**: _(Document any unexpected findings here)_

---

### Step 2: Write Integration Tests for Logout CSRF (TDD - Test First)

**File**: `backend/tests/integration/test_csrf_routes.py`

**Reference**: Specification lines 750-927

#### Test 1: Logout requires CSRF token

- [ ] Write test: `test_logout_requires_csrf_token`
  - Login user first (to get valid session)
  - Attempt POST `/logout` without CSRF token
  - Assert: response.status_code == 403
  - Assert: Error message mentions CSRF or security validation
  - Assert: Session still valid (user NOT logged out)

#### Test 2: Logout with valid CSRF token succeeds

- [ ] Write test: `test_logout_with_valid_csrf_token`
  - Login user first
  - GET `/settings` to obtain CSRF token
  - Extract token from cookie and HTML hidden input
  - POST `/logout` with valid token in both cookie and form field
  - Assert: response.status_code == 303 (redirect)
  - Assert: response.headers["Location"] == "/login"
  - Assert: access_token cookie is cleared

#### Test 3: Failed logout preserves session

- [ ] Write test: `test_logout_failed_attempt_preserves_session`
  - Login user first
  - Attempt POST `/logout` WITHOUT CSRF token (attack scenario)
  - Assert: response.status_code == 403
  - GET `/chat/` to verify user still authenticated
  - Assert: response.status_code == 200 (not redirected to login)
  - Assert: Page contains logout button (user still logged in)

#### Test 4: Logout with invalid token fails

- [ ] Write test: `test_logout_with_invalid_token`
  - Login user first
  - GET `/settings` to obtain legitimate CSRF token
  - Tamper with token (use fake value like "tampered_invalid_token_12345")
  - POST `/logout` with tampered token
  - Assert: response.status_code == 403

#### Verify Tests Fail

- [ ] Run integration tests (should FAIL - no implementation yet)
  ```bash
  uv --directory backend run pytest tests/integration/test_csrf_routes.py::test_logout_requires_csrf_token -v
  uv --directory backend run pytest tests/integration/test_csrf_routes.py::test_logout_with_valid_csrf_token -v
  uv --directory backend run pytest tests/integration/test_csrf_routes.py::test_logout_failed_attempt_preserves_session -v
  uv --directory backend run pytest tests/integration/test_csrf_routes.py::test_logout_with_invalid_token -v
  ```
- [ ] Verify all 4 tests fail with expected errors (no CSRF validation yet)

#### Commit

- [ ] Commit tests
  ```bash
  git add backend/tests/integration/test_csrf_routes.py
  git commit -m "test: Add integration tests for logout CSRF protection

- Test logout requires CSRF token (403 without token)
- Test logout succeeds with valid token
- Test failed logout preserves session
- Test logout with invalid token fails

Tests currently fail - implementation in next commit"
  ```

---

### Step 3: Update Backend Routes (TDD - Implementation)

**Reference**: Specification lines 336-360, 369-441

#### Update /logout endpoint

**File**: `backend/app/routes/auth.py`

- [ ] Locate `@router.post("/logout")` function (line ~276)
- [ ] Add required imports at top of file:
  ```python
  from fastapi_csrf_protect.flexible import CsrfProtect
  ```
- [ ] Add CSRF dependencies to function signature:
  ```python
  @router.post("/logout")
  async def logout(
      request: Request,
      csrf_protect: CsrfProtect = Depends(),
  ) -> Response:
  ```
- [ ] Add CSRF validation as FIRST line in function:
  ```python
  """Logout user by clearing authentication cookie.

  CSRF protection prevents attackers from forcing logout via malicious sites.
  """
  # Validate CSRF token
  await csrf_protect.validate_csrf(request)

  response = Response(status_code=status.HTTP_303_SEE_OTHER)
  response.headers["Location"] = "/login"
  response.delete_cookie(key="access_token")
  return response
  ```

#### Update GET /settings endpoint

**File**: `backend/app/routes/dashboard.py`

- [ ] Locate `@router.get("/settings")` function (line ~49)
- [ ] Add required imports at top of file:
  ```python
  from fastapi_csrf_protect.flexible import CsrfProtect
  from app.dependencies import get_templates
  ```
- [ ] Add CSRF dependency to function signature:
  ```python
  @router.get("/settings", response_class=HTMLResponse)
  async def settings_page(
      request: Request,
      user: UserResponse = Depends(get_current_user),
      csrf_protect: CsrfProtect = Depends(),
      templates: Jinja2Templates = Depends(get_templates),
  ) -> Response:
  ```
- [ ] Generate CSRF tokens and set cookie:
  ```python
  """Settings hub page with Garmin and profile management links.

  Requires authentication via get_current_user dependency.
  Generates CSRF token for logout form protection.
  """
  # Generate CSRF token pair for logout form
  csrf_token, signed_token = csrf_protect.generate_csrf_tokens()

  response = templates.TemplateResponse(
      request=request,
      name="settings.html",
      context={"user": user, "csrf_token": csrf_token},
  )

  # Set CSRF cookie
  csrf_protect.set_csrf_cookie(signed_token, response)

  return response
  ```

#### Update GET /chat/ endpoint

**File**: `backend/app/routes/chat.py`

- [ ] Locate `@router.get("/")` function (line ~20)
- [ ] Add required imports at top of file:
  ```python
  from fastapi_csrf_protect.flexible import CsrfProtect
  from app.dependencies import get_templates
  ```
- [ ] Add CSRF dependency to function signature:
  ```python
  @router.get("/", response_class=HTMLResponse)
  async def chat_page(
      request: Request,
      current_user: UserResponse = Depends(get_current_user),
      csrf_protect: CsrfProtect = Depends(),
      templates: Jinja2Templates = Depends(get_templates),
  ) -> Response:
  ```
- [ ] Generate CSRF tokens and set cookie:
  ```python
  """Render chat interface page.

  Generates CSRF token for logout form and future chat send protection.
  """
  # Generate CSRF token pair
  csrf_token, signed_token = csrf_protect.generate_csrf_tokens()

  response = templates.TemplateResponse(
      "chat.html",
      {"request": request, "user": current_user, "csrf_token": csrf_token},
  )

  # Set CSRF cookie
  csrf_protect.set_csrf_cookie(signed_token, response)

  return response
  ```

#### Verify Tests Pass

- [ ] Run integration tests (should now PASS)
  ```bash
  uv --directory backend run pytest tests/integration/test_csrf_routes.py::test_logout_requires_csrf_token -v
  uv --directory backend run pytest tests/integration/test_csrf_routes.py::test_logout_with_valid_csrf_token -v
  uv --directory backend run pytest tests/integration/test_csrf_routes.py::test_logout_failed_attempt_preserves_session -v
  uv --directory backend run pytest tests/integration/test_csrf_routes.py::test_logout_with_invalid_token -v
  ```
- [ ] Verify all 4 tests pass

**Note**: Tests may still fail because templates don't have CSRF token fields yet. That's expected - we'll fix in next step.

#### Commit

- [ ] Commit backend changes
  ```bash
  git add backend/app/routes/auth.py backend/app/routes/dashboard.py backend/app/routes/chat.py
  git commit -m "feat: Add CSRF protection to logout endpoint

- Add CSRF validation to POST /logout endpoint
- Generate CSRF tokens in GET /settings endpoint
- Generate CSRF tokens in GET /chat/ endpoint
- Prevents forced logout attacks from malicious sites

Ref: SPECIFICATION.md lines 336-441"
  ```

---

### Step 4: Update Templates with CSRF Tokens

**Reference**: Specification lines 391-441

#### Update settings.html

**File**: `backend/app/templates/settings.html`

- [ ] Locate logout form (line ~16)
- [ ] Add hidden CSRF token input field as FIRST field in form:
  ```html
  <form method="POST" action="/logout" class="inline">
      <input type="hidden" name="fastapi-csrf-token" value="{{ csrf_token }}">
      <button type="submit"
              class="text-sm text-red-600 hover:text-red-800"
              data-testid="logout-button"
              aria-label="Logout">
          Logout
      </button>
  </form>
  ```

#### Update chat.html

**File**: `backend/app/templates/chat.html`

- [ ] Locate logout form (line ~30)
- [ ] Add hidden CSRF token input field as FIRST field in form:
  ```html
  <form method="POST" action="/logout" class="inline">
      <input type="hidden" name="fastapi-csrf-token" value="{{ csrf_token }}">
      <button
          type="submit"
          class="bg-gray-100 text-gray-700 hover:bg-gray-200 font-medium px-4 py-2 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition duration-150"
          data-testid="logout-button"
          aria-label="Logout from your account"
      >
          Logout
      </button>
  </form>
  ```

#### Verify All Tests Pass

- [ ] Run all integration tests for logout
  ```bash
  uv --directory backend run pytest tests/integration/test_csrf_routes.py -k logout -v
  ```
- [ ] Verify all logout tests pass (4 tests should pass)

#### Commit

- [ ] Commit template changes
  ```bash
  git add backend/app/templates/settings.html backend/app/templates/chat.html
  git commit -m "feat: Add CSRF tokens to logout forms

- Add hidden csrf token field to settings.html logout form
- Add hidden csrf token field to chat.html logout form
- Tokens generated by GET endpoints in previous commit

Completes logout CSRF protection implementation"
  ```

---

### Step 5: Verify CSRF Cookie Configuration

**Goal**: Ensure CSRF cookie settings are correct for JavaScript access (needed for Phase 2)

**Reference**: Specification lines 623-633

- [ ] Verify cookie configuration in `backend/app/main.py`
  ```bash
  grep -A10 "class CsrfSettings" /Users/bryn/repos/selflytics/backend/app/main.py
  ```
- [ ] Check for:
  - `cookie_httponly: bool = False` (line ~53) - MUST be False for JavaScript
  - `cookie_samesite: str = "strict"` (line ~51) - Should be strict for security
  - `cookie_secure: bool = True` (line ~52) - Should be True in production

**Expected Result**: Configuration already correct from PR #21 (no changes needed)

- [ ] Document configuration status: _(Is config correct? Any issues?)_

---

### Step 6: Run Full Test Suite

**Goal**: Ensure no regressions in existing functionality

- [ ] Run all tests
  ```bash
  uv --directory backend run pytest tests/ -v --cov=app
  ```
- [ ] Verify:
  - All tests pass (0 failures)
  - Coverage ≥ 80%
  - No new warnings

**If tests fail**: Debug and fix issues before proceeding. Ask user if you need help.

#### Commit (if any fixes needed)

- [ ] If fixes were needed, commit them:
  ```bash
  git add <fixed-files>
  git commit -m "fix: <description of fix>"
  ```

---

### Step 7: Manual Testing Verification

**Goal**: Verify CSRF protection works in actual browser

#### Test 1: Verify CSRF tokens in forms

- [ ] Start dev server: `./scripts/dev-server.sh`
- [ ] Navigate to http://localhost:8000/login
- [ ] Login with valid credentials
- [ ] Navigate to http://localhost:8000/settings
- [ ] Open browser DevTools → Elements tab
- [ ] Inspect logout form
- [ ] Verify: `<input type="hidden" name="fastapi-csrf-token" value="...">` exists
- [ ] Verify: Token value is non-empty (32+ characters)
- [ ] Open DevTools → Application tab → Cookies
- [ ] Verify: `fastapi-csrf-token` cookie exists with value

#### Test 2: Verify legitimate logout works

- [ ] Click logout button in settings page
- [ ] Verify: Redirected to /login page
- [ ] Verify: No error messages shown
- [ ] Verify: access_token cookie is cleared (check DevTools → Cookies)

#### Test 3: Verify forged logout is blocked

- [ ] Login again to get fresh session
- [ ] Open browser DevTools → Console tab
- [ ] Run JavaScript to simulate CSRF attack:
  ```javascript
  fetch('/logout', {
    method: 'POST',
    headers: {'Content-Type': 'application/x-www-form-urlencoded'},
    // No CSRF token - simulates cross-site attack
    body: ''
  }).then(r => console.log('Status:', r.status))
  ```
- [ ] Verify: Console shows "Status: 403" (blocked)
- [ ] Navigate to /chat/ to verify still logged in
- [ ] Verify: Chat page loads successfully (not redirected to login)
- [ ] Verify: Logout button still visible

#### Test 4: Verify chat page logout form

- [ ] While on /chat/ page, open DevTools → Elements
- [ ] Inspect logout form in header
- [ ] Verify: Hidden CSRF token input field exists
- [ ] Click logout button
- [ ] Verify: Successful logout and redirect to /login

#### Manual Testing Results

- [ ] Document results: _(All tests passed? Any issues?)_

---

### Step 8: Code Quality Checks

**Goal**: Ensure code meets quality standards

#### Type Checking

- [ ] Run mypy
  ```bash
  uv run mypy backend/app
  ```
- [ ] Verify: No type errors

#### Linting

- [ ] Run ruff check
  ```bash
  uv run ruff check .
  ```
- [ ] Verify: No linting errors
- [ ] If errors found, run auto-fix:
  ```bash
  uv run ruff check . --fix
  ```

#### Formatting

- [ ] Run ruff format
  ```bash
  uv run ruff format .
  ```
- [ ] Verify: Code properly formatted

#### Security Scan

- [ ] Run bandit
  ```bash
  uv run bandit -c backend/pyproject.toml -r backend/app/ -ll
  ```
- [ ] Verify: No security warnings

#### Commit Quality Fixes

- [ ] If any auto-fixes were applied:
  ```bash
  git add -A
  git commit -m "chore: Code quality fixes (ruff, mypy)"
  ```

---

### Step 9: Update Phase Plan Status

- [ ] Mark all checkboxes in this plan as complete
- [ ] Update step statuses:
  - Change ⏳ NEXT markers to ✅ DONE
  - Update any session summaries or notes
- [ ] Update phase status at top of document to ✅ DONE

---

### Step 10: Final Commit and Push

- [ ] Review all changes:
  ```bash
  git log --oneline chore/csrf-improvements..HEAD
  git diff chore/csrf-improvements...HEAD
  ```
- [ ] Verify commit history is clean and descriptive
- [ ] Push to origin:
  ```bash
  git push origin chore/csrf-improvements-phase-1
  ```
- [ ] Create PR to `chore/csrf-improvements` (not main)
  - Title: "Phase 1: Protect Logout Endpoint"
  - Description: Reference this phase plan and spec lines 189-441
  - Link to issue #12

---

## Success Criteria

### Functional

- [x] `/logout` endpoint validates CSRF token
- [x] Settings page logout form includes CSRF token
- [x] Chat page logout form includes CSRF token
- [x] Logout without token returns 403 and preserves session
- [x] Logout with valid token succeeds

### Testing

- [x] Integration test: logout requires CSRF token (403 without)
- [x] Integration test: logout succeeds with valid token
- [x] Integration test: failed logout preserves session
- [x] Integration test: logout with invalid token fails
- [x] Manual test: CSRF token visible in HTML (DevTools)
- [x] Manual test: legitimate logout works
- [x] Manual test: forged logout blocked

### Quality

- [x] All tests pass (integration + existing)
- [x] Coverage ≥ 80% maintained
- [x] No type errors (mypy)
- [x] No linting errors (ruff)
- [x] No security warnings (bandit)

---

## Notes

### Design Decisions

- **Form-based CSRF**: Logout uses form field (not header) because it's a traditional HTML form submission
- **Token in context**: GET endpoints pass `csrf_token` to template context for rendering in hidden input
- **Cookie + Field**: Both cookie and form field required for Double Submit Cookie pattern
- **Error handling**: Existing CSRF exception handler in `main.py` handles 403 responses

### Spec References

- Logout endpoint protection: Specification lines 336-360
- Settings page changes: Specification lines 369-401
- Chat page changes: Specification lines 407-441
- Cookie configuration: Specification lines 623-633
- Integration tests: Specification lines 750-927

### Common Patterns (from PR #21)

- Import: `from fastapi_csrf_protect.flexible import CsrfProtect`
- Dependency: `csrf_protect: CsrfProtect = Depends()`
- Validation: `await csrf_protect.validate_csrf(request)`
- Generation: `csrf_token, signed_token = csrf_protect.generate_csrf_tokens()`
- Set cookie: `csrf_protect.set_csrf_cookie(signed_token, response)`
- Template: `<input type="hidden" name="fastapi-csrf-token" value="{{ csrf_token }}">`

---

## Dependencies for Next Phase

Phase 2 needs from Phase 1:
- ✅ CSRF cookie configuration verified (httponly=false)
- ✅ GET /chat/ endpoint generates CSRF tokens
- ✅ CSRF token available in chat.html template context

---

**End of Phase 1 Plan**
