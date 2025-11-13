# Phase 4: E2E Test Fixes & User Journey Verification

**Branch**: `feat/phase-4-e2e-fixes`
**Status**: 🔄 IN PROGRESS (Session 1 of 2)

---

## Session 1 Summary (2025-11-14)

**Completed**: 4 commits, ~3 hours
**Progress**: Infrastructure fixes and backend HTMX support complete
**See**: `docs/project-setup/PHASE_4_SESSION_1_PROGRESS.md` for detailed summary

### ✅ Completed Work

1. **Port Configuration** (commit `71556d3`)
   - Configured `.env.local` with non-conflicting ports (8042 web, 8092 Firestore)
   - Updated dev-server.sh and local-e2e-server.sh scripts
   - Prevents port conflicts during local e2e testing

2. **Mock Fixture Fix** (commit `6c5d84a`)
   - Fixed `mock_garmin_api` to only intercept POST requests
   - GET requests now pass through to real backend for form rendering
   - Fixed bytes vs string comparison for Playwright compatibility

3. **Backend HTMX Support** (commit `a8f9c2b`)
   - Converted POST /garmin/link to return HTML fragments
   - Converted POST /garmin/sync to return HTML fragments
   - Changed to accept Form(...) data instead of JSON
   - Added proper data-testid attributes to HTML responses

---

## Session 2 Summary (2025-11-14)

**Completed**: 1 commit, ~1 hour
**Progress**: Fixed URL encoding issue in mock fixture - 5 tests now passing (up from 1)

### ✅ Completed Work

1. **URL Encoding Fix** (commit: "fix(test): handle URL-encoded form data in Garmin mock")
   - Fixed mock_garmin_api fixture to handle URL-encoded form data
   - Browser sends `test%40garmin.com` (@ becomes %40) in form submissions
   - Mock now checks for both raw and URL-encoded email addresses
   - This fixed `test_new_user_links_garmin_account` which was failing at form submission

### 🔄 Current Status

**Test Progress**: 5 passing, 11 failing (out of 16 total)

**Passing Tests**:
- ✅ `test_required_fields_validation` (HTML5 client validation)
- ✅ `test_email_format_validation` (HTML5 client validation)
- ✅ `test_password_field_masked` (accessibility)
- ✅ `test_focus_visible_on_inputs` (accessibility)
- ✅ `test_new_user_links_garmin_account` (main user journey) 🎉

**Failing Tests Pattern**: Most failures timeout waiting for `[data-testid="input-garmin-username"]`
- Root cause: Tests using `authenticated_user` fixture but setting up their own route handlers
- These tests navigate to `/garmin/link` but form doesn't appear (authentication or routing issue)
- Need to investigate fixture interaction and authentication persistence

**Next Session Goal**:
1. Fix remaining 11 test failures (mostly fixture/authentication issues)
2. Verify all 16 tests passing
3. Create manual testing runsheet
4. Create E2E testing documentation
5. Final validation and phase completion

---

## Goal

Fix all 16 failing e2e tests and verify complete user journeys work end-to-end. Establish robust e2e testing infrastructure for local development and CI validation.

**Key Deliverables:**
- All 16 Playwright e2e tests passing locally
- Missing `data-testid` attributes added to templates
- Manual runsheet for user journey validation
- E2E test documentation and troubleshooting guide

---

## Prerequisites

**Previous Phases:**
- ✅ Phase 1: Infrastructure Foundation (auth, frontend, deployment)
- ✅ Phase 2: Garmin Integration (OAuth, token management, caching)
- ✅ Phase 3: Chat + AI Agent (Pydantic-AI, conversation management)

**Local Environment:**
- ✅ Branch created: `feat/phase-4-e2e-fixes`
- ✅ `.env.local` configured with ports 8042/8092
- ✅ Firebase emulator and dev server scripts updated
- ✅ Playwright installed and working

---

## Deliverables

### Investigation Outputs
- ✅ Test failure analysis (via debug-investigator)
- ✅ Root cause identification (mock fixture + backend responses)
- ⬜ Missing `data-testid` inventory (templates already have them)

### Code Changes
- ✅ All templates have proper `data-testid` attributes (verified)
- ✅ E2E test infrastructure improvements (port config, mock fixes)
- 🔄 Test reliability fixes (in progress - POST submission issue)

### Documentation
- ⬜ Manual testing runsheet for user journeys
- ⬜ E2E testing guide for local development
- ⬜ Troubleshooting guide for common failures

---

## Implementation Steps

### Setup

- [x] ✅ Create branch `feat/phase-4-e2e-fixes`
- [x] ✅ Verify local environment ready:
  - [x] Firebase emulator running (`./scripts/local-e2e-server.sh`)
  - [x] Dev server running (started by local-e2e-server.sh)
  - [x] Playwright installed and working

---

### ⏳ NEXT: Fix Remaining 11 E2E Test Failures

**Current Problem**:
- 5 tests passing, 11 tests failing (out of 16 total)
- Most failures: Timeout waiting for `[data-testid="input-garmin-username"]` (30s timeout)
- Root cause hypothesis: Tests using `authenticated_user` fixture then setting up their own route handlers
- Form not appearing when tests navigate to `/garmin/link` after authentication

**Failing Tests**:
1. `test_valid_form_submits` - can't find Garmin username input
2. `test_server_rejects_invalid_credentials` - can't find Garmin username input
3. `test_keyboard_navigation` - can't focus on Garmin username input
4. `test_user_can_retry_after_error` - can't find Garmin username input
5. `test_linking_with_invalid_credentials` - can't find Garmin username input
6. `test_unauthenticated_user_redirected` - not redirecting to /login properly
7. `test_manual_sync_success` - can't find Garmin username input
8. `test_link_form_uses_htmx_not_full_reload` - can't find Garmin username input
9. `test_sync_button_htmx_request` - can't find Garmin username input
10. `test_loading_state_during_submission` - can't find submit button
11. `test_error_displayed_inline_no_reload` - can't find Garmin username input

**Debug Strategy**:
1. Use debug-investigator to run one failing test in headed mode and observe:
   - Does `/garmin/link` page load correctly?
   - Is the user actually authenticated (check cookies/session)?
   - Are route handlers conflicting (test's handler vs mock_garmin_api)?
   - What HTML is actually rendered when test navigates to `/garmin/link`?

2. Check if tests need to use `user_with_garmin_unlinked` fixture instead of `authenticated_user`

3. Verify that navigation after authentication preserves session cookies

4. Consider if tests should use `mock_garmin_api` fixture instead of setting up their own handlers

---

### Step 1: Investigate Test Failures (✅ COMPLETED)

**File**: Analysis document

- [ ] Run e2e tests with verbose output: `uv run pytest backend/tests/e2e_playwright -v --tb=short`
- [ ] Capture failure details for each test class:
  - [ ] `TestGarminLinkingJourney` (4 tests)
  - [ ] `TestGarminSyncJourney` (1 test)
  - [ ] `TestHTMXPartialUpdates` (3 tests)
  - [ ] `TestAlpineJSLoadingStates` (1 test)
  - [ ] `TestHTMXErrorHandling` (1 test)
  - [ ] `TestHTML5ClientValidation` (3 tests)
  - [ ] `TestServerSideValidation` (1 test)
  - [ ] `TestInputBehaviorAndAccessibility` (3 tests)
  - [ ] `TestErrorRecoveryFlows` (1 test)
- [ ] Document patterns:
  - Which tests fail at fixture setup vs. during test execution?
  - What selectors are they looking for?
  - Are failures consistent or intermittent?
- [ ] Commit: "docs: document e2e test failure patterns"

**Expected Findings:**
- Most tests fail during `authenticated_user` fixture setup (conftest.py line 78)
- Timeout waiting for `[data-testid="register-link"]` suggests:
  - Server not responding at base_url
  - Login page not rendering correctly
  - HTMX/Alpine.js not initialized
  - Page navigation broken

---

### Step 2: Debug with @agent-debug-investigator

**Investigator Tasks:**

- [ ] Task 1: Verify server is accessible at base_url
  - [ ] Check `backend/.env` has correct PORT
  - [ ] Verify server responds to `http://localhost:{PORT}`
  - [ ] Check login page renders at `http://localhost:{PORT}/login`
- [ ] Task 2: Verify `data-testid="register-link"` exists on login page
  - [ ] Inspect `backend/app/templates/login.html` line 94
  - [ ] Load page in browser, check rendered HTML
  - [ ] Verify Alpine.js/HTMX loaded (check browser console)
- [ ] Task 3: Check base_url fixture logic in conftest.py
  - [ ] Review priority: TEST_BASE_URL → BASE_URL → PORT → default
  - [ ] Verify .env.local or .env exists in backend/
  - [ ] Check if PORT conflicts with running server
- [ ] Task 4: Test minimal Playwright script
  - [ ] Create standalone test: navigate to base_url, screenshot, check for register-link
  - [ ] Run outside pytest to isolate fixture issues
- [ ] Document findings in `docs/development/e2e-debugging-log.md`
- [ ] Commit: "docs: e2e debugging investigation results"

**Likely Root Causes:**
1. **Base URL mismatch**: Test expects `http://localhost:8000`, server runs on different port
2. **Server not running**: Tests run but server isn't started
3. **HTMX not loaded**: CDN blocked or base.html missing script tags
4. **Timing issue**: Page renders but Playwright checks too early (before HTMX ready)

---

### Step 3: Fix Root Cause Issues

**Based on investigation, implement fixes:**

#### Fix 3a: Base URL Configuration (if mismatch found)

**File**: `backend/.env.local` (create if missing)

- [ ] Create `.env.local` with TEST settings:
  ```bash
  PORT=8000
  BASE_URL=http://localhost:8000
  ENVIRONMENT=test
  DEBUG=true
  ```
- [ ] Update `.gitignore` to exclude `.env.local`
- [ ] Document in `backend/README.md`: "For e2e tests, copy `.env.example` to `.env.local`"
- [ ] Commit: "fix: add .env.local for e2e test configuration"

#### Fix 3b: Server Startup Check (if server not running)

**File**: `backend/tests/e2e_playwright/conftest.py`

- [ ] Add health check fixture:
  ```python
  @pytest.fixture(scope="session", autouse=True)
  def ensure_server_running(base_url: str):
      """Verify dev server is running before tests start."""
      import requests
      from requests.exceptions import ConnectionError

      try:
          response = requests.get(f"{base_url}/health", timeout=5)
          assert response.status_code == 200, f"Server health check failed: {response.status_code}"
      except ConnectionError:
          pytest.fail(
              f"Dev server not running at {base_url}. "
              "Start it with: ./scripts/dev-server.sh"
          )
  ```
- [ ] Commit: "test: add server health check for e2e tests"

#### Fix 3c: Page Load Wait Strategy (if timing issue)

**File**: `backend/tests/e2e_playwright/conftest.py`

- [ ] Update `authenticated_user` fixture to wait for page ready:
  ```python
  @pytest.fixture
  def authenticated_user(page: Page, base_url: str, test_user: dict):
      """Register and login a test user."""
      # Navigate with wait for network idle
      page.goto(base_url, wait_until="networkidle")

      # Wait for register link with better error message
      try:
          page.wait_for_selector('[data-testid="register-link"]', state="visible", timeout=10000)
      except Exception as e:
          # Take screenshot for debugging
          page.screenshot(path="./test-artifacts/failed-page-load.png")
          raise AssertionError(
              f"Register link not found at {base_url}. "
              f"Check screenshot at test-artifacts/failed-page-load.png"
          ) from e

      page.click('[data-testid="register-link"]')
      # ... rest of fixture
  ```
- [ ] Create `test-artifacts/` directory (add to .gitignore)
- [ ] Commit: "test: improve page load wait strategy in e2e fixtures"

---

### Step 4: Audit and Add Missing data-testid Attributes

**Files**: All templates in `backend/app/templates/`

- [ ] Create inventory of all interactive elements needing test IDs
- [ ] Review each template:

#### Template: `base.html`

**File**: `backend/app/templates/base.html`

- [ ] Check if file exists and has navigation elements
- [ ] Add `data-testid` to any nav links:
  ```html
  <a href="/dashboard" data-testid="nav-dashboard">Dashboard</a>
  <a href="/chat" data-testid="nav-chat">Chat</a>
  <a href="/settings/garmin" data-testid="nav-garmin">Garmin</a>
  ```
- [ ] Commit: "test: add data-testid to base template navigation"

#### Template: `login.html`

**File**: `backend/app/templates/login.html`

- [ ] ✅ VERIFIED: Line 94 has `data-testid="register-link"` (already exists)
- [ ] ✅ VERIFIED: Form has `data-testid="login-form"` (line 21)
- [ ] ✅ VERIFIED: Inputs have `data-testid="input-email"` and `data-testid="input-password"`
- [ ] ✅ VERIFIED: Submit button has `data-testid="submit-login"`
- [ ] No changes needed (already compliant)

#### Template: `register.html`

**File**: `backend/app/templates/register.html`

- [ ] ✅ VERIFIED: Form has `data-testid="register-form"` (line 21)
- [ ] ✅ VERIFIED: All inputs have proper `data-testid` attributes
- [ ] ✅ VERIFIED: Submit button has `data-testid="submit-register"`
- [ ] ✅ VERIFIED: Login link has `data-testid="link-login"` (line 158)
- [ ] No changes needed (already compliant)

#### Template: `dashboard.html`

**File**: `backend/app/templates/dashboard.html`

- [ ] ✅ VERIFIED: Has `data-testid="dashboard-header"` (line 8)
- [ ] ✅ VERIFIED: Has `data-testid="welcome-section"` (line 33)
- [ ] ✅ VERIFIED: Has `data-testid="logout-button"` (line 20)
- [ ] Check if Garmin "Connect Now" button needs test ID:
  ```html
  <a href="/settings/garmin" data-testid="button-connect-garmin" class="bg-blue-600...">
      Connect Now
  </a>
  ```
- [ ] Commit: "test: add data-testid to dashboard Garmin connect button"

#### Template: `settings_garmin.html`

**File**: `backend/app/templates/settings_garmin.html`

- [ ] ✅ VERIFIED: Form has `data-testid="form-link-garmin"` (line 49)
- [ ] ✅ VERIFIED: Inputs have `data-testid="input-garmin-username"` and `data-testid="input-garmin-password"`
- [ ] ✅ VERIFIED: Submit has `data-testid="submit-link-garmin"`
- [ ] ✅ VERIFIED: Linked state has `data-testid="garmin-status-linked"` (line 11)
- [ ] ✅ VERIFIED: Sync button has `data-testid="button-sync-garmin"` (line 23)
- [ ] No changes needed (already compliant)

#### Template: `chat.html`

**File**: `backend/app/templates/chat.html`

- [ ] Add test IDs to chat interface elements:
  ```html
  <button data-testid="button-new-chat" @click="newConversation()">New Chat</button>
  <div data-testid="messages-container" id="messages">...</div>
  <input data-testid="input-message" x-model="messageInput" type="text">
  <button data-testid="button-send-message" type="submit">Send</button>
  ```
- [ ] Add test IDs to conversation list:
  ```html
  <div data-testid="conversation-list" class="space-y-2">
      <template x-for="conv in conversations">
          <div data-testid="conversation-item" @click="loadConversation(...)">
  ```
- [ ] Commit: "test: add data-testid to chat interface elements"

---

### Step 5: Create Unit/Integration Tests with @agent-test-quality-reviewer

**Goal**: Add tests to cover gaps in coverage revealed by e2e test scenarios

#### Test 5a: HTMX Response Format Tests

**File**: `backend/tests/integration/routers/test_garmin_htmx.py`

- [ ] Write tests for HTMX-specific responses:
  - [ ] Test `/garmin/link` POST returns HTML fragment (not JSON)
  - [ ] Test response has `data-testid` attributes
  - [ ] Test response has correct `hx-swap` targets
  - [ ] Test error responses return HTML fragments with error classes
- [ ] Review with @agent-test-quality-reviewer:
  - Check test scenarios cover all HTMX endpoints
  - Verify assertions check `Content-Type: text/html`
  - Ensure error cases tested (invalid credentials, Garmin API down)
- [ ] Verify tests fail (no implementation changes yet)
- [ ] Run tests: `uv run pytest backend/tests/integration/routers/test_garmin_htmx.py -v`
- [ ] Commit: "test: add HTMX response format integration tests"

#### Test 5b: Template Rendering Tests

**File**: `backend/tests/unit/test_template_rendering.py`

- [ ] Write tests for template `data-testid` attributes:
  - [ ] Test login template has all required test IDs
  - [ ] Test register template has all required test IDs
  - [ ] Test settings_garmin template has all required test IDs
  - [ ] Test dashboard template has all required test IDs
- [ ] Use FastAPI TestClient to render templates:
  ```python
  def test_login_template_has_register_link(client):
      response = client.get("/login")
      assert response.status_code == 200
      assert 'data-testid="register-link"' in response.text
  ```
- [ ] Review with @agent-test-quality-reviewer
- [ ] Run tests: `uv run pytest backend/tests/unit/test_template_rendering.py -v`
- [ ] Commit: "test: add template rendering validation tests"

#### Test 5c: Alpine.js State Management Tests

**File**: `backend/tests/e2e_playwright/test_alpine_state.py`

- [ ] Write tests for Alpine.js reactive state:
  - [ ] Test form `loading` state toggles button text
  - [ ] Test form `loading` state disables inputs
  - [ ] Test Alpine `x-show` directives work correctly
- [ ] Use Playwright to evaluate JavaScript state:
  ```python
  def test_alpine_loading_state(authenticated_user: Page):
      # Fill form but don't submit
      page.fill('[data-testid="input-garmin-username"]', "test@example.com")

      # Check Alpine state
      loading_state = page.evaluate("() => Alpine.store('formState')?.loading")
      assert loading_state is False
  ```
- [ ] Review with @agent-test-quality-reviewer
- [ ] Run tests: `uv run pytest backend/tests/e2e_playwright/test_alpine_state.py -v`
- [ ] Commit: "test: add Alpine.js state management e2e tests"

---

### Step 6: Fix Identified Issues

**Based on test failures from Step 5, implement fixes:**

- [ ] Fix any missing `data-testid` attributes found by template tests
- [ ] Fix any HTMX response format issues (content-type, HTML structure)
- [ ] Fix any Alpine.js initialization issues
- [ ] Verify all unit/integration tests now pass
- [ ] Commit: "fix: resolve issues found by new test coverage"

---

### Step 7: Run Full E2E Test Suite

**Verify all 16 tests pass:**

- [ ] Start fresh environment:
  ```bash
  # Terminal 1: Emulators
  ./scripts/start-emulators.sh

  # Terminal 2: Dev server
  ./scripts/dev-server.sh

  # Terminal 3: E2E tests
  uv run pytest backend/tests/e2e_playwright -v --tb=short
  ```
- [ ] Document results in `docs/development/e2e-test-results.md`:
  - [ ] Screenshot of all tests passing
  - [ ] Timing information (slowest tests)
  - [ ] Any warnings or issues to address
- [ ] If any tests fail:
  - [ ] Debug with `--headed` flag: `uv run pytest backend/tests/e2e_playwright -v --headed`
  - [ ] Check screenshots in `test-artifacts/`
  - [ ] Review Playwright trace (if configured)
  - [ ] Fix issues and re-run
- [ ] Commit: "test: all 16 e2e tests passing"

**Expected Output:**
```
backend/tests/e2e_playwright/test_garmin_linking_journey.py::TestGarminLinkingJourney::test_new_user_links_garmin_account PASSED
backend/tests/e2e_playwright/test_garmin_linking_journey.py::TestGarminLinkingJourney::test_linking_with_invalid_credentials PASSED
backend/tests/e2e_playwright/test_garmin_linking_journey.py::TestGarminLinkingJourney::test_unauthenticated_user_redirected PASSED
backend/tests/e2e_playwright/test_garmin_linking_journey.py::TestGarminSyncJourney::test_manual_sync_success PASSED
backend/tests/e2e_playwright/test_htmx_interactions.py::TestHTMXPartialUpdates::test_link_form_uses_htmx_not_full_reload PASSED
backend/tests/e2e_playwright/test_htmx_interactions.py::TestHTMXPartialUpdates::test_sync_button_htmx_request PASSED
backend/tests/e2e_playwright/test_htmx_interactions.py::TestAlpineJSLoadingStates::test_loading_state_during_submission PASSED
backend/tests/e2e_playwright/test_htmx_interactions.py::TestHTMXErrorHandling::test_error_displayed_inline_no_reload PASSED
backend/tests/e2e_playwright/test_form_validation.py::TestHTML5ClientValidation::test_required_fields_validation PASSED
backend/tests/e2e_playwright/test_form_validation.py::TestHTML5ClientValidation::test_email_format_validation PASSED
backend/tests/e2e_playwright/test_form_validation.py::TestHTML5ClientValidation::test_valid_form_submits PASSED
backend/tests/e2e_playwright/test_form_validation.py::TestServerSideValidation::test_server_rejects_invalid_credentials PASSED
backend/tests/e2e_playwright/test_form_validation.py::TestInputBehaviorAndAccessibility::test_password_field_masked PASSED
backend/tests/e2e_playwright/test_form_validation.py::TestInputBehaviorAndAccessibility::test_keyboard_navigation PASSED
backend/tests/e2e_playwright/test_form_validation.py::TestInputBehaviorAndAccessibility::test_focus_visible_on_inputs PASSED
backend/tests/e2e_playwright/test_form_validation.py::TestErrorRecoveryFlows::test_user_can_retry_after_error PASSED

======================== 16 passed in 45.23s ========================
```

---

### Step 8: Create Manual Testing Runsheet

**File**: `docs/development/MANUAL_TESTING_RUNSHEET.md`

- [ ] Create comprehensive manual test checklist:

```markdown
# Manual Testing Runsheet - User Journeys

**Purpose**: Validate complete user flows work end-to-end with real user interactions

**Prerequisites**:
- [ ] Emulators running (`./scripts/start-emulators.sh`)
- [ ] Dev server running (`./scripts/dev-server.sh`)
- [ ] Browser open to http://localhost:8000

---

## Journey 1: New User Registration → Garmin Linking

**Scenario**: First-time user signs up and connects Garmin account

1. **Navigate to Home**
   - [ ] Open http://localhost:8000
   - [ ] Verify redirected to /login
   - [ ] Verify login form visible

2. **Navigate to Registration**
   - [ ] Click "Register" link
   - [ ] Verify redirected to /register
   - [ ] Verify registration form visible with 4 fields

3. **Fill Registration Form**
   - [ ] Enter Display Name: "Test User"
   - [ ] Enter Email: "test-manual-{timestamp}@example.com"
   - [ ] Enter Password: "TestPass123!"
   - [ ] Enter Confirm Password: "TestPass123!"
   - [ ] Verify form fields accept input
   - [ ] Verify password fields masked

4. **Submit Registration**
   - [ ] Click "Create Account" button
   - [ ] Verify button shows "Creating Account..." with spinner
   - [ ] Verify redirected to /dashboard (HTMX HX-Redirect)
   - [ ] Verify welcome message: "Welcome back, Test User!"

5. **Check Garmin Status**
   - [ ] Verify banner: "Connect Your Garmin Account"
   - [ ] Verify "Connect Now" button visible

6. **Navigate to Garmin Settings**
   - [ ] Click "Connect Now" button
   - [ ] Verify redirected to /settings/garmin (or /garmin/link)
   - [ ] Verify form: "Link Your Garmin Account"

7. **Link Garmin Account**
   - [ ] Enter Garmin Email: "test@garmin.com" (mock credentials)
   - [ ] Enter Garmin Password: "password123"
   - [ ] Click "Link Account" button
   - [ ] Verify button shows "Linking..." with spinner
   - [ ] Verify success message: "Garmin account linked"
   - [ ] Verify "Sync Now" button appears
   - [ ] Verify form no longer visible (HTMX swap)

8. **Manual Sync**
   - [ ] Click "Sync Now" button
   - [ ] Verify success message: "Sync completed successfully"

**Expected Result**: ✅ User registered, logged in, linked Garmin, and synced data

---

## Journey 2: Returning User Login → Chat

**Scenario**: Existing user logs in and starts chat conversation

1. **Login with Existing Credentials**
   - [ ] Navigate to /login
   - [ ] Enter email from Journey 1
   - [ ] Enter password: "TestPass123!"
   - [ ] Click "Login" button
   - [ ] Verify redirected to /dashboard

2. **Navigate to Chat**
   - [ ] Click "Chat Analysis" card (if enabled)
   - [ ] OR navigate to /chat directly
   - [ ] Verify chat interface loads

3. **Start New Conversation**
   - [ ] Click "New Chat" button
   - [ ] Verify messages area empty
   - [ ] Verify input field focused

4. **Send Message**
   - [ ] Type: "How am I doing?"
   - [ ] Click "Send" button
   - [ ] Verify user message appears (right-aligned, blue)
   - [ ] Verify loading indicator ("AI is thinking...")
   - [ ] Verify AI response appears (left-aligned, gray)
   - [ ] Verify conversation added to sidebar

5. **Continue Conversation**
   - [ ] Type: "Show me my activities"
   - [ ] Press Enter key (not button)
   - [ ] Verify message sent
   - [ ] Verify AI responds with activity data

6. **Load Conversation History**
   - [ ] Click conversation in sidebar
   - [ ] Verify messages load
   - [ ] Verify scroll to bottom

**Expected Result**: ✅ User logged in, chatted with AI, viewed history

---

## Journey 3: Error Handling & Recovery

**Scenario**: User encounters errors and recovers gracefully

1. **Registration with Invalid Data**
   - [ ] Navigate to /register
   - [ ] Enter short password: "123"
   - [ ] Click "Create Account"
   - [ ] Verify HTML5 validation error (client-side)
   - [ ] Verify form still editable

2. **Registration with Duplicate Email**
   - [ ] Use email from Journey 1
   - [ ] Fill valid password
   - [ ] Click "Create Account"
   - [ ] Verify server error message (HTMX swap)
   - [ ] Verify error is red and visible

3. **Login with Wrong Password**
   - [ ] Navigate to /login
   - [ ] Enter valid email, wrong password
   - [ ] Click "Login"
   - [ ] Verify error message: "Invalid credentials"
   - [ ] Verify form still visible (can retry)

4. **Garmin Link with Invalid Credentials**
   - [ ] Login successfully
   - [ ] Navigate to /settings/garmin
   - [ ] Enter: "wrong@garmin.com", "wrongpass"
   - [ ] Click "Link Account"
   - [ ] Verify error message (HTMX swap)
   - [ ] Verify error mentions "invalid credentials"

5. **Retry After Error**
   - [ ] Correct credentials: "test@garmin.com", "password123"
   - [ ] Click "Link Account"
   - [ ] Verify success message
   - [ ] Verify error message gone

**Expected Result**: ✅ Errors displayed clearly, user can recover

---

## Journey 4: Accessibility & Keyboard Navigation

**Scenario**: User navigates entirely with keyboard

1. **Tab Navigation (Registration)**
   - [ ] Navigate to /register
   - [ ] Press Tab repeatedly
   - [ ] Verify focus order: Display Name → Email → Password → Confirm → Submit
   - [ ] Verify focus outlines visible

2. **Keyboard Form Submission**
   - [ ] Fill display name, press Tab
   - [ ] Fill email, press Tab
   - [ ] Fill password, press Tab
   - [ ] Fill confirm password, press Enter
   - [ ] Verify form submits (no button click needed)

3. **Screen Reader Compatibility**
   - [ ] Enable screen reader (VoiceOver on Mac, NVDA on Windows)
   - [ ] Navigate form with screen reader
   - [ ] Verify labels announced correctly
   - [ ] Verify error messages announced (aria-live)
   - [ ] Verify required fields announced

**Expected Result**: ✅ Full keyboard navigation, accessible to screen readers

---

## Post-Journey Verification

**Database State** (optional - check Firebase Emulator UI):
- [ ] Open http://localhost:4000 (Emulator UI)
- [ ] Check Firestore > users collection
- [ ] Verify test user exists with correct email
- [ ] Check garmin_tokens collection
- [ ] Verify token exists for test user (if linked)

**Cleanup**:
- [ ] Stop dev server (Ctrl+C)
- [ ] Stop emulators (Ctrl+C)
- [ ] Clear emulator data: `./scripts/clear-emulator-data.sh` (if script exists)

---

## Sign-Off

**Tester**: _________________
**Date**: _________________
**All Journeys Passed**: ☐ Yes  ☐ No

**Issues Found**:
- Issue 1: ____________________________
- Issue 2: ____________________________

**Notes**:
```

- [ ] Commit: "docs: add manual testing runsheet for user journeys"

---

### Step 9: Execute Manual Testing Runsheet

**With User** (if available):

- [ ] Schedule manual testing session with user
- [ ] Share runsheet: `docs/development/MANUAL_TESTING_RUNSHEET.md`
- [ ] User executes all 4 journeys
- [ ] User documents any issues found
- [ ] Capture user feedback on UX/UI
- [ ] Fix critical issues found (if any)

**Solo Testing** (if no user available):

- [ ] Execute runsheet yourself as end-user
- [ ] Step through each journey methodically
- [ ] Check boxes as you go
- [ ] Screenshot any issues
- [ ] Document issues in runsheet "Issues Found" section
- [ ] Create GitHub issues for non-critical items (label: `ux-improvement`)

- [ ] Save completed runsheet with timestamp: `MANUAL_TESTING_RUNSHEET_2025-11-14.md`
- [ ] Commit: "docs: completed manual testing runsheet - all journeys verified"

---

### Step 10: Create E2E Testing Documentation

**File**: `docs/development/E2E_TESTING_GUIDE.md`

- [ ] Write comprehensive guide for developers:

```markdown
# E2E Testing Guide

**Purpose**: How to run, debug, and maintain Playwright e2e tests locally

## Quick Start

**Prerequisites**:
1. Firebase emulators running: `./scripts/start-emulators.sh`
2. Dev server running: `./scripts/dev-server.sh`
3. Playwright installed: `uv sync --all-extras`

**Run All E2E Tests**:
```bash
uv run pytest backend/tests/e2e_playwright -v
```

**Run Specific Test Class**:
```bash
uv run pytest backend/tests/e2e_playwright/test_garmin_linking_journey.py::TestGarminLinkingJourney -v
```

**Run Single Test**:
```bash
uv run pytest backend/tests/e2e_playwright/test_garmin_linking_journey.py::TestGarminLinkingJourney::test_new_user_links_garmin_account -v
```

---

## Debugging Test Failures

### 1. Run in Headed Mode (see browser)

```bash
uv run pytest backend/tests/e2e_playwright -v --headed
```

This opens browser windows so you can see what Playwright is doing.

### 2. Enable Slow Motion

```bash
uv run pytest backend/tests/e2e_playwright -v --headed --slowmo 1000
```

Slows down actions by 1000ms (1 second) each.

### 3. Take Screenshots on Failure

Already enabled in conftest.py. Check `test-artifacts/` for screenshots.

### 4. Use Playwright Inspector

```bash
PWDEBUG=1 uv run pytest backend/tests/e2e_playwright::test_name -v
```

Opens Playwright Inspector for step-by-step debugging.

### 5. Check Server Logs

If tests timeout, check dev server logs:
- Look for 500 errors
- Check for database connection issues
- Verify HTMX responses return HTML (not JSON)

---

## Common Issues & Solutions

### Issue: "Timeout waiting for [data-testid='register-link']"

**Cause**: Server not running or base_url misconfigured

**Solution**:
1. Verify server running: `curl http://localhost:8000/health`
2. Check `backend/.env.local` has correct PORT
3. Verify `conftest.py` base_url fixture returns correct URL

### Issue: "HTMX swap didn't happen"

**Cause**: HTMX not loaded or response format wrong

**Solution**:
1. Check browser console for HTMX errors
2. Verify base.html includes HTMX script tag
3. Check server response Content-Type is `text/html` (not `application/json`)

### Issue: "Alpine.js state not updating"

**Cause**: Alpine not initialized or syntax error

**Solution**:
1. Check browser console for Alpine errors
2. Verify base.html includes Alpine.js script tag
3. Verify `x-data` directive on parent element

---

## Test Organization

```
backend/tests/e2e_playwright/
├── conftest.py                    # Fixtures (authenticated_user, base_url, etc.)
├── test_garmin_linking_journey.py # User journey: register → link Garmin
├── test_htmx_interactions.py      # HTMX-specific behaviors
├── test_form_validation.py        # Client + server validation
└── test_alpine_state.py           # Alpine.js reactive state
```

---

## Writing New E2E Tests

**Pattern: Journey-Driven**

Focus on complete user flows, not isolated interactions.

**Good** ✅:
```python
def test_user_can_link_garmin_account(authenticated_user: Page):
    """Complete journey: dashboard → settings → link → verify"""
    # ... full flow
```

**Bad** ❌:
```python
def test_garmin_button_exists(page: Page):
    """Just checks a button exists"""
    # Too granular, should be unit test
```

**Use Fixtures**:
- `page`: Fresh browser page
- `base_url`: Correct URL for environment
- `test_user`: Unique user credentials
- `authenticated_user`: Logged-in user (ready to test)
- `mock_garmin_api`: Mocked Garmin API responses

**Best Practices**:
1. Use `data-testid` selectors (not CSS classes)
2. Wait for state changes explicitly (`expect().to_be_visible()`)
3. Check URL changes for navigation (`page.wait_for_url()`)
4. Verify HTMX swaps completed (check for new content)
5. Clean up test data (delete test users in fixture teardown)

---

## CI Integration

E2E tests run in GitHub Actions on:
- Every PR to main
- Push to main
- Nightly schedule

**CI Differences**:
- Uses TEST_BASE_URL (deployed preview environment)
- Headless mode (no browser window)
- Screenshots uploaded as artifacts on failure

**Check CI Results**:
1. Go to GitHub Actions tab
2. Find your PR workflow run
3. Check "E2E Tests" job
4. Download artifacts if tests failed
```

- [ ] Commit: "docs: add comprehensive e2e testing guide"

---

### Step 11: Final Validation

**Quality Checks**:

- [ ] Run full test suite (all categories):
  ```bash
  # Unit tests
  uv run pytest backend/tests/unit -v --cov=app

  # Integration tests
  uv run pytest backend/tests/integration -v

  # E2E tests
  uv run pytest backend/tests/e2e_playwright -v
  ```
- [ ] Verify coverage maintained (>80%):
  ```bash
  uv run pytest --cov=app --cov-report=term-missing --cov-fail-under=80
  ```
- [ ] Run linting:
  ```bash
  uv run ruff check .
  uv run ruff format --check .
  ```
- [ ] Run type checking:
  ```bash
  uv run mypy backend/app --strict
  ```
- [ ] Run security scan:
  ```bash
  uv run bandit -c backend/pyproject.toml -r backend/app/ -ll
  ```
- [ ] All checks pass
- [ ] Commit: "Phase 4 complete: all e2e tests passing, user journeys verified"

---

### Step 12: Update Roadmap

**File**: `docs/project-setup/ROADMAP.md`

- [ ] Update Phase 4 status to ✅ DONE
- [ ] Add actual time to "Actual Time" column
- [ ] Update "Current Phase" section to point to next phase
- [ ] Add entry to History table:
  ```markdown
  | 2025-11-14 | Phase 4 completed ✅ | All 16 e2e tests passing, user journeys verified, manual runsheet completed (X hours) |
  ```
- [ ] Commit: "docs: update roadmap - Phase 4 complete"

---

## Testing Requirements

**Unit Test Coverage**:
- Template rendering validation: 100%
- HTMX response format tests: 100%
- Data-testid attribute checks: 100%

**Integration Test Coverage**:
- All HTMX endpoints return HTML fragments: 100%
- Error responses formatted correctly: 100%

**E2E Test Coverage**:
- All 16 existing tests pass: 100%
- New tests for chat interface (if applicable): 80%

**Overall Coverage Target**: Maintain >80% (should increase with new tests)

---

## Success Criteria

### Technical Success

- [ ] All 16 Playwright e2e tests passing locally
- [ ] E2E tests can be run by any developer (`README` instructions work)
- [ ] Test failures provide clear error messages and screenshots
- [ ] All templates have required `data-testid` attributes
- [ ] Unit/integration tests cover HTMX and template rendering

### User Journey Success

- [ ] Manual runsheet completed (all journeys verified working)
- [ ] User can register → login → link Garmin → sync → chat (if enabled)
- [ ] Error handling graceful (clear messages, can retry)
- [ ] Accessibility verified (keyboard nav, screen reader compatible)

### Documentation Success

- [ ] E2E testing guide clear and actionable
- [ ] Troubleshooting guide covers common issues
- [ ] Manual runsheet can be used by non-developers
- [ ] Future developers can write new e2e tests following patterns

---

## Dependencies for Next Phase

**Phase 5 (Visualization Generation - Future)** will need:
- E2E tests for chart generation journeys
- Manual testing of generated visualizations
- Visual regression testing (screenshot comparison)

This phase provides the foundation for testing those features.

---

## Notes

**Key Design Decisions**:

1. **Journey-driven e2e tests**: Focus on complete user flows, not isolated interactions
   - Rationale: E2E tests are expensive (slow), so test complete value delivery
   - Alternative: Playwright component tests for isolated widget testing

2. **Mock Garmin API in e2e**: Don't call real Garmin API
   - Rationale: Tests must be repeatable, fast, and not depend on external services
   - Alternative: E2E tests against real Garmin staging API (slower, flakier)

3. **Manual runsheet in addition to e2e**: Human testing catches UX issues
   - Rationale: Automated tests check functionality, humans check usability
   - Alternative: Only automated tests (misses UX problems)

4. **data-testid instead of CSS selectors**: Stable test selectors
   - Rationale: UI styling changes shouldn't break tests
   - Alternative: CSS class selectors (brittle, couples tests to styles)

**Lessons from Investigation**:

- Most e2e test failures are infrastructure issues (server not running), not code bugs
- Clear error messages in fixtures save hours of debugging
- Screenshots on failure are essential for async Playwright debugging
- Base URL configuration is the #1 source of confusion

---

**Phase Status**: Ready for Implementation
**Last Updated**: 2025-11-14
