# Phase 3: E2E Tests & Security Validation

**Branch**: `feat/csrf-phase-3`
**Status**: PLANNED
**Estimated Time**: 1.5 hours
**Dependencies**: Phase 1 & 2 (all routes protected)

---

## Goal

Validate CSRF protection end-to-end with Playwright tests covering real attack scenarios. This phase adds comprehensive E2E tests, manual testing runsheet execution, and security validation to ensure CSRF protection works correctly across all user journeys.

**Key Deliverables**:
- E2E test: Cross-origin POST attack blocked (Garmin link scenario)
- E2E test: Token rotation on validation errors
- E2E test: HTMX partial updates preserve CSRF tokens
- Manual testing runsheet completed
- Security scan passes (bandit)
- Full system validation

**Security Impact**:
- Validates attack prevention works in real browser environment
- Confirms HTMX compatibility doesn't break CSRF protection
- Ensures token rotation prevents replay attacks
- Provides regression testing for future changes

---

## Prerequisites

**Required Before Starting**:
- [ ] Phase 1 & 2 complete and merged into `feat/csrf`
- [ ] All POST routes protected (/auth/register, /auth/login, /garmin/link, /garmin/sync)
- [ ] Token rotation working on all error paths
- [ ] All unit + integration tests passing

**Specification Context**:
- Lines 655-729: User Journey 2 - CSRF Attack Blocked (Garmin Link)
- Lines 733-799: User Journey 3 - Form Validation Error (Token Refresh)
- Lines 1075-1157: E2E Tests (Playwright)
- Lines 1160-1200: Manual Testing Checklist

**Codebase Context**:
- E2E tests: `backend/tests/e2e_playwright/`
- Existing E2E patterns: `test_user_journeys.py`, `test_garmin_linking_journey.py`
- Playwright fixtures: `backend/tests/e2e_playwright/conftest.py`
- Local E2E script: `./scripts/local-e2e-server.sh`

---

## Deliverables

### New Files
- [ ] `backend/tests/e2e_playwright/test_csrf_protection.py` - E2E CSRF tests (3 journey tests)
- [ ] `docs/development/csrf/MANUAL_TESTING_RUNSHEET.md` - Manual verification checklist

### Modified Files
- None (E2E tests are additive)

---

## Implementation Steps

### Setup

- [x] ~~NEXT:~~ Create branch from feat/csrf
  ```bash
  git checkout feat/csrf
  git pull origin feat/csrf  # Ensure Phase 1 & 2 merged
  git checkout -b feat/csrf-phase-3
  ```

- [x] Verify local E2E environment setup:
  ```bash
  # Check Firestore emulator installed
  firebase --version
  # Check Playwright browsers installed
  uv --directory backend run playwright install chromium
  ```

---

### Step 1: E2E Test - Cross-Origin POST Attack Blocked

**Goal**: Verify CSRF protection blocks malicious cross-origin POST requests (User Journey 2 from spec)

**File**: `backend/tests/e2e_playwright/test_csrf_protection.py`

#### Implementation

- [ ] Create new E2E test file:
  ```python
  """E2E tests for CSRF protection."""

  import pytest
  from playwright.sync_api import Page, expect


  @pytest.mark.e2e
  def test_csrf_blocks_cross_origin_garmin_link_attack(
      page: Page,
      base_url: str,
      authenticated_page: Page,
  ):
      """Test that cross-origin POST to /garmin/link is blocked by CSRF protection.

      This test simulates the HIGH-RISK attack scenario from spec lines 102-168:
      - Attacker creates malicious page with auto-submitting form
      - Victim (logged into Selflytics) visits malicious page
      - Browser auto-sends victim's auth cookie with POST request
      - CSRF protection BLOCKS the request (no valid CSRF token)
      - Victim's account remains secure (attacker's Garmin account NOT linked)

      Reference: Spec lines 655-729 (Journey 2 - CSRF Attack Blocked)
      """

      # STEP 1: User logs into Selflytics (authenticated_page fixture handles this)
      authenticated_page.goto(f"{base_url}/dashboard")
      expect(authenticated_page).to_have_url(f"{base_url}/dashboard")

      # STEP 2: Verify user can access Garmin link page (shows form)
      authenticated_page.goto(f"{base_url}/garmin/link")
      expect(authenticated_page.locator('[data-testid="form-link-garmin"]')).to_be_visible()

      # STEP 3: Simulate attacker's malicious page
      # This page auto-submits a form to /garmin/link without CSRF token
      malicious_html = f"""
      <!DOCTYPE html>
      <html>
      <head><title>Malicious Page</title></head>
      <body onload="document.forms[0].submit()">
          <h1>Loading...</h1>
          <form action="{base_url}/garmin/link" method="POST" id="attack-form">
              <input type="hidden" name="username" value="attacker@evil.com">
              <input type="hidden" name="password" value="AttackerGarminPass123">
              <!-- NO csrf_token - this is the attack! -->
          </form>
      </body>
      </html>
      """

      # Navigate to malicious page (simulates clicking phishing link)
      authenticated_page.set_content(malicious_html)

      # STEP 4: Wait for form auto-submission to complete
      authenticated_page.wait_for_load_state("networkidle")

      # STEP 5: Verify attack was BLOCKED
      # Check if we're still on the malicious page or got redirected to error
      # The key is that /garmin/link should NOT have processed the request

      # Navigate back to Garmin link page to verify account NOT linked
      authenticated_page.goto(f"{base_url}/garmin/link")

      # Verify Garmin link FORM is still showing (not success message)
      # If attack succeeded, we'd see "Garmin account linked" success message
      expect(authenticated_page.locator('[data-testid="form-link-garmin"]')).to_be_visible()

      # Verify no success indicators
      expect(authenticated_page.locator("text=Successfully linked")).not_to_be_visible()
      expect(authenticated_page.locator("text=Garmin account linked")).not_to_be_visible()

      # STEP 6: Additional verification - check for CSRF error in logs or response
      # Note: In Playwright, we can't easily inspect 403 response from cross-origin form
      # But the fact that form is still showing proves attack failed


  @pytest.mark.e2e
  def test_csrf_blocks_cross_origin_register_attack(
      page: Page,
      base_url: str,
  ):
      """Test that cross-origin POST to /auth/register is blocked.

      Simpler attack scenario (no authentication required) to verify
      CSRF protection works on registration endpoint.

      Reference: Spec lines 175-203 (Forced Account Registration attack)
      """

      # STEP 1: Navigate to legitimate registration page
      page.goto(f"{base_url}/register")
      expect(page.locator('[data-testid="register-form"]')).to_be_visible()

      # STEP 2: Simulate attacker's page trying to create spam accounts
      malicious_html = f"""
      <!DOCTYPE html>
      <html>
      <body onload="submitAttack()">
          <h1>Processing...</h1>
          <iframe name="hidden-frame" style="display:none"></iframe>
          <form action="{base_url}/auth/register" method="POST" target="hidden-frame">
              <input type="hidden" name="email" value="spam-001@tempmail.com">
              <input type="hidden" name="password" value="SpamPass123">
              <input type="hidden" name="display_name" value="Spam User">
              <input type="hidden" name="confirm_password" value="SpamPass123">
              <!-- NO csrf_token -->
          </form>
          <script>
              function submitAttack() {
                  document.forms[0].submit();
              }
          </script>
      </body>
      </html>
      """

      page.set_content(malicious_html)
      page.wait_for_timeout(1000)  # Wait for iframe submission

      # STEP 3: Verify attack failed - try to login with spam credentials
      page.goto(f"{base_url}/login")
      page.fill('[data-testid="input-email"]', "spam-001@tempmail.com")
      page.fill('[data-testid="input-password"]', "SpamPass123")
      page.click('[data-testid="submit-login"]')

      # Login should FAIL (account not created)
      page.wait_for_timeout(500)
      # Should see error or stay on login page
      expect(page.locator("text=Incorrect email or password")).to_be_visible()
  ```

- [ ] Run E2E test locally:
  ```bash
  # Start Firestore emulator + dev server in one terminal
  ./scripts/local-e2e-server.sh

  # In another terminal, run E2E test
  uv --directory backend run pytest tests/e2e_playwright/test_csrf_protection.py::test_csrf_blocks_cross_origin_garmin_link_attack -v --headed
  ```

- [ ] Verify test passes (attack blocked)

- [ ] Commit E2E attack prevention test:
  ```bash
  git add backend/tests/e2e_playwright/test_csrf_protection.py
  git commit -m "test(e2e): verify CSRF blocks cross-origin POST attacks"
  ```

**Success Criteria**:
- [ ] E2E test passes (attack blocked)
- [ ] Test runs in headless and headed mode
- [ ] Test verifies both Garmin link and registration attacks fail
- [ ] Test execution time < 30 seconds

**Reference**: Spec lines 1086-1121, 655-729

**Time Estimate**: 30 minutes

---

### Step 2: E2E Test - Token Rotation on Validation Errors

**Goal**: Verify CSRF tokens are rotated on form validation errors (User Journey 3 from spec)

**File**: `backend/tests/e2e_playwright/test_csrf_protection.py`

#### Implementation

- [ ] Add token rotation test to test file:
  ```python
  @pytest.mark.e2e
  def test_csrf_token_rotation_on_validation_error(
      page: Page,
      base_url: str,
  ):
      """Test that CSRF token is rotated when form has validation errors.

      Verifies token rotation prevents replay attacks by ensuring each
      form submission gets a fresh token after validation errors.

      Reference: Spec lines 733-799 (Journey 3 - Form Validation Error)
      """

      # STEP 1: Navigate to registration page
      page.goto(f"{base_url}/register")
      expect(page.locator('[data-testid="register-form"]')).to_be_visible()

      # STEP 2: Extract initial CSRF token from hidden field
      csrf_input = page.locator('input[name="csrf_token"]')
      expect(csrf_input).to_be_hidden()
      token1 = csrf_input.get_attribute("value")

      assert token1 is not None
      assert len(token1) >= 32  # Sufficient entropy

      # STEP 3: Fill form with password MISMATCH (validation error)
      page.fill('[data-testid="input-email"]', "test@example.com")
      page.fill('[data-testid="input-display-name"]', "Test User")
      page.fill('[data-testid="input-password"]', "Pass123")
      page.fill('[data-testid="input-confirm-password"]', "Pass456")  # MISMATCH!

      # STEP 4: Submit form (will fail validation)
      page.click('[data-testid="submit-register"]')

      # STEP 5: Wait for HTMX to swap form with error message
      page.wait_for_timeout(500)
      expect(page.locator("text=Passwords do not match")).to_be_visible()

      # STEP 6: Extract NEW CSRF token from re-rendered form
      csrf_input2 = page.locator('input[name="csrf_token"]')
      token2 = csrf_input2.get_attribute("value")

      assert token2 is not None
      assert len(token2) >= 32

      # STEP 7: Verify token was ROTATED (different from original)
      assert token2 != token1, "CSRF token should be rotated after validation error"

      # STEP 8: Correct the password and submit with NEW token
      page.fill('[data-testid="input-password"]', "Pass123")
      page.fill('[data-testid="input-confirm-password"]', "Pass123")  # Fixed!
      page.click('[data-testid="submit-register"]')

      # STEP 9: Verify successful registration (redirects to dashboard)
      page.wait_for_url(f"{base_url}/dashboard", timeout=5000)
      expect(page).to_have_url(f"{base_url}/dashboard")


  @pytest.mark.e2e
  def test_csrf_token_rotation_on_login_failure(
      page: Page,
      base_url: str,
      test_user: dict,
  ):
      """Test that CSRF token is rotated on login authentication failure.

      Reference: Spec lines 733-799
      """

      # STEP 1: Navigate to login page
      page.goto(f"{base_url}/login")
      expect(page.locator('[data-testid="login-form"]')).to_be_visible()

      # STEP 2: Extract initial token
      token1 = page.locator('input[name="csrf_token"]').get_attribute("value")
      assert token1 is not None

      # STEP 3: Submit with WRONG password
      page.fill('[data-testid="input-email"]', test_user["email"])
      page.fill('[data-testid="input-password"]', "WrongPassword123")
      page.click('[data-testid="submit-login"]')

      # STEP 4: Wait for error
      page.wait_for_timeout(500)
      expect(page.locator("text=Incorrect email or password")).to_be_visible()

      # STEP 5: Verify token rotated
      token2 = page.locator('input[name="csrf_token"]').get_attribute("value")
      assert token2 != token1, "Token should rotate on auth failure"

      # STEP 6: Login with CORRECT password and new token
      page.fill('[data-testid="input-password"]', test_user["password"])
      page.click('[data-testid="submit-login"]')

      # STEP 7: Verify success
      page.wait_for_url(f"{base_url}/dashboard", timeout=5000)
  ```

- [ ] Run E2E tests locally:
  ```bash
  uv --directory backend run pytest tests/e2e_playwright/test_csrf_protection.py -v -k rotation --headed
  ```

- [ ] Verify both rotation tests pass

- [ ] Commit token rotation tests:
  ```bash
  git add backend/tests/e2e_playwright/test_csrf_protection.py
  git commit -m "test(e2e): verify CSRF token rotation on validation errors"
  ```

**Success Criteria**:
- [ ] Both rotation tests pass
- [ ] Tests verify tokens change after errors
- [ ] Tests verify forms work correctly with rotated tokens
- [ ] Tests execution time < 20 seconds total

**Reference**: Spec lines 1123-1142, 733-799

**Time Estimate**: 20 minutes

---

### Step 3: E2E Test - HTMX Partial Updates Preserve Tokens

**Goal**: Verify CSRF tokens work correctly with HTMX partial DOM updates

**File**: `backend/tests/e2e_playwright/test_csrf_protection.py`

#### Implementation

- [ ] Add HTMX compatibility test:
  ```python
  @pytest.mark.e2e
  def test_csrf_token_works_with_htmx_partial_updates(
      page: Page,
      base_url: str,
      authenticated_page: Page,
  ):
      """Test that CSRF tokens are preserved and rotated correctly with HTMX partial updates.

      HTMX swaps HTML fragments without full page reloads. This test verifies:
      1. Token included in initial partial render
      2. Token rotated when fragment is swapped after error
      3. New token works for subsequent submission

      Reference: Spec lines 461-577 (HTMX Integration)
      """

      # STEP 1: Navigate to Garmin link page (uses HTMX)
      authenticated_page.goto(f"{base_url}/garmin/link")
      expect(authenticated_page.locator('[data-testid="form-link-garmin"]')).to_be_visible()

      # STEP 2: Verify CSRF token exists in form
      csrf_input = authenticated_page.locator('input[name="csrf_token"]')
      expect(csrf_input).to_be_hidden()
      token1 = csrf_input.get_attribute("value")
      assert token1 is not None

      # STEP 3: Submit form with INVALID Garmin credentials
      # This triggers HTMX partial update (hx-swap="outerHTML")
      authenticated_page.fill('[data-testid="input-garmin-username"]', "test@garmin.com")
      authenticated_page.fill('[data-testid="input-garmin-password"]', "WrongPassword")
      authenticated_page.click('[data-testid="submit-link-garmin"]')

      # STEP 4: Wait for HTMX to swap form fragment
      authenticated_page.wait_for_timeout(500)

      # Verify error message displayed (form was swapped)
      expect(authenticated_page.locator("text=Please check your credentials")).to_be_visible()

      # STEP 5: Verify form still exists (HTMX swapped it, not full page reload)
      expect(authenticated_page.locator('[data-testid="form-link-garmin"]')).to_be_visible()

      # STEP 6: Verify NEW token exists in swapped fragment
      csrf_input2 = authenticated_page.locator('input[name="csrf_token"]')
      token2 = csrf_input2.get_attribute("value")
      assert token2 is not None

      # STEP 7: Verify token was ROTATED by HTMX swap
      assert token2 != token1, "Token should be rotated after HTMX fragment swap"

      # STEP 8: Verify CSRF cookie was also updated
      # (fastapi-csrf-protect sets cookie in response headers, HTMX respects this)
      cookies = authenticated_page.context.cookies()
      csrf_cookie = next((c for c in cookies if c["name"] == "csrf_token"), None)
      assert csrf_cookie is not None
      # Note: Can't easily verify cookie changed, but presence confirms it's set

      # STEP 9: (Optional) Submit again with correct credentials if test Garmin available
      # For now, just verify form is functional with new token
      authenticated_page.fill('[data-testid="input-garmin-password"]', "AnotherWrongPass")
      authenticated_page.click('[data-testid="submit-link-garmin"]')
      authenticated_page.wait_for_timeout(500)

      # Verify another token rotation occurred
      token3 = authenticated_page.locator('input[name="csrf_token"]').get_attribute("value")
      assert token3 != token2, "Token should rotate on each error"
  ```

- [ ] Run HTMX compatibility test:
  ```bash
  uv --directory backend run pytest tests/e2e_playwright/test_csrf_protection.py::test_csrf_token_works_with_htmx_partial_updates -v --headed
  ```

- [ ] Verify test passes

- [ ] Commit HTMX compatibility test:
  ```bash
  git add backend/tests/e2e_playwright/test_csrf_protection.py
  git commit -m "test(e2e): verify CSRF tokens work with HTMX partial updates"
  ```

**Success Criteria**:
- [ ] Test passes (tokens preserved across HTMX swaps)
- [ ] Test verifies token rotation on each fragment swap
- [ ] Test confirms form remains functional after multiple swaps
- [ ] Test execution time < 15 seconds

**Reference**: Spec lines 1144-1157, 461-577

**Time Estimate**: 15 minutes

---

### Step 4: Manual Testing Runsheet

**Goal**: Create and execute comprehensive manual testing checklist

**File**: `docs/development/csrf/MANUAL_TESTING_RUNSHEET.md`

#### Implementation

- [ ] Create manual testing runsheet:
  ```markdown
  # CSRF Protection Manual Testing Runsheet

  **Date**: ___________
  **Tester**: ___________
  **Environment**: Local Development (http://localhost:8000)
  **Status**: ⏳ IN PROGRESS / ✅ COMPLETE

  ---

  ## Setup

  - [ ] Firestore emulator running: `firebase emulators:start --only firestore`
  - [ ] Dev server running: `./scripts/dev-server.sh`
  - [ ] Browser DevTools open (Chrome/Edge recommended)
  - [ ] Test user account created (email: test@example.com, password: TestPass123)

  ---

  ## Test 1: Verify CSRF Tokens in Forms

  **Goal**: Confirm CSRF tokens are present and correctly formatted in all forms

  ### Registration Form
  - [ ] Navigate to http://localhost:8000/register
  - [ ] Open DevTools → Elements tab
  - [ ] Locate `<input type="hidden" name="csrf_token">`
  - [ ] Verify token value is non-empty string (32+ characters)
  - [ ] Open DevTools → Application → Cookies
  - [ ] Verify `csrf_token` cookie exists with value matching hidden field (signed version)
  - [ ] **Result**: PASS / FAIL
  - **Notes**: ___________________________________________

  ### Login Form
  - [ ] Navigate to http://localhost:8000/login
  - [ ] Verify `<input name="csrf_token">` exists
  - [ ] Verify csrf_token cookie exists
  - [ ] **Result**: PASS / FAIL

  ### Garmin Link Form (requires login)
  - [ ] Login with test credentials
  - [ ] Navigate to http://localhost:8000/garmin/link
  - [ ] Verify `<input name="csrf_token">` exists in Garmin form
  - [ ] Verify csrf_token cookie exists
  - [ ] **Result**: PASS / FAIL

  ---

  ## Test 2: Verify CSRF Protection Blocks Forged Requests

  **Goal**: Confirm cross-origin POST requests without valid CSRF token are blocked

  ### Attack Scenario: Garmin Link (HIGH PRIORITY)

  **Preparation**:
  - [ ] Create file `csrf-attack-garmin.html` with content:
    ```html
    <!DOCTYPE html>
    <html>
    <head><title>Malicious Page</title></head>
    <body onload="document.forms[0].submit()">
        <h1>Loading...</h1>
        <form action="http://localhost:8000/garmin/link" method="POST">
            <input type="hidden" name="username" value="attacker@evil.com">
            <input type="hidden" name="password" value="AttackerPass123">
        </form>
    </body>
    </html>
    ```
  - [ ] Save file to desktop

  **Execution**:
  - [ ] Login to Selflytics (http://localhost:8000/login)
  - [ ] Verify logged in (dashboard visible)
  - [ ] Open `csrf-attack-garmin.html` in browser (File → Open)
  - [ ] Wait for auto-submission
  - [ ] Open DevTools → Network tab
  - [ ] Verify POST to /garmin/link shows 403 Forbidden status
  - [ ] Navigate back to http://localhost:8000/garmin/link
  - [ ] Verify form still shows (NOT success message)
  - [ ] Verify no Garmin account linked
  - [ ] **Result**: PASS / FAIL (CRITICAL TEST)
  - **Evidence**: Screenshot of 403 response: ___________

  ### Attack Scenario: Registration

  **Preparation**:
  - [ ] Create file `csrf-attack-register.html`:
    ```html
    <!DOCTYPE html>
    <html>
    <body onload="document.forms[0].submit()">
        <form action="http://localhost:8000/auth/register" method="POST">
            <input type="hidden" name="email" value="spam@test.com">
            <input type="hidden" name="password" value="Spam123">
            <input type="hidden" name="display_name" value="Spam">
            <input type="hidden" name="confirm_password" value="Spam123">
        </form>
    </body>
    </html>
    ```

  **Execution**:
  - [ ] Open `csrf-attack-register.html`
  - [ ] Wait for submission
  - [ ] Try to login with spam@test.com / Spam123
  - [ ] Verify login FAILS (account not created)
  - [ ] **Result**: PASS / FAIL

  ---

  ## Test 3: Verify Legitimate Requests Succeed

  **Goal**: Confirm CSRF protection doesn't break normal user flows

  ### Registration Flow
  - [ ] Navigate to http://localhost:8000/register
  - [ ] Fill form completely:
    - Email: newuser@example.com
    - Display Name: New User
    - Password: NewPass123
    - Confirm Password: NewPass123
  - [ ] Submit form
  - [ ] Verify redirected to /dashboard (successful registration)
  - [ ] Verify no errors displayed
  - [ ] **Result**: PASS / FAIL

  ### Login Flow
  - [ ] Logout (if logged in)
  - [ ] Navigate to http://localhost:8000/login
  - [ ] Enter credentials: newuser@example.com / NewPass123
  - [ ] Submit form
  - [ ] Verify redirected to /dashboard
  - [ ] **Result**: PASS / FAIL

  ### Garmin Link Flow (if test Garmin account available)
  - [ ] Login to Selflytics
  - [ ] Navigate to /garmin/link
  - [ ] Enter Garmin credentials
  - [ ] Submit form
  - [ ] Verify success message or appropriate error (not CSRF error)
  - [ ] **Result**: PASS / FAIL / SKIP (no test Garmin)

  ---

  ## Test 4: Verify Token Rotation on Errors

  **Goal**: Confirm CSRF tokens are regenerated after validation/auth errors

  ### Registration Password Mismatch
  - [ ] Navigate to http://localhost:8000/register
  - [ ] Copy csrf_token value from hidden field (DevTools)
    - **Token 1**: ___________________________________________
  - [ ] Fill form with password MISMATCH:
    - Email: rotate@test.com
    - Display Name: Rotate Test
    - Password: Pass123
    - Confirm Password: Pass456  ← MISMATCH
  - [ ] Submit form
  - [ ] Verify error: "Passwords do not match"
  - [ ] Copy NEW csrf_token value from hidden field
    - **Token 2**: ___________________________________________
  - [ ] Verify Token 2 ≠ Token 1 (rotation occurred)
  - [ ] Open DevTools → Network → Find POST request
  - [ ] Verify response includes `Set-Cookie: csrf_token=...` (new cookie)
  - [ ] Correct password to Pass123 and submit
  - [ ] Verify successful registration
  - [ ] **Result**: PASS / FAIL

  ### Login Invalid Credentials
  - [ ] Navigate to http://localhost:8000/login
  - [ ] Copy csrf_token value
    - **Token 1**: ___________________________________________
  - [ ] Enter: test@example.com / WrongPassword
  - [ ] Submit form
  - [ ] Verify error: "Incorrect email or password"
  - [ ] Copy NEW csrf_token value
    - **Token 2**: ___________________________________________
  - [ ] Verify Token 2 ≠ Token 1
  - [ ] Enter correct password and submit
  - [ ] Verify successful login
  - [ ] **Result**: PASS / FAIL

  ---

  ## Test 5: Verify HTMX Compatibility

  **Goal**: Confirm CSRF tokens work with HTMX partial DOM updates

  ### HTMX Form Swap (Garmin Link)
  - [ ] Login to Selflytics
  - [ ] Navigate to /garmin/link
  - [ ] Open DevTools → Network tab
  - [ ] Clear network log
  - [ ] Submit form with wrong Garmin credentials
  - [ ] In Network tab, find POST to /garmin/link
  - [ ] Verify response is HTML fragment (not full page)
  - [ ] Verify response includes `Set-Cookie: csrf_token=...`
  - [ ] Verify form re-rendered with error (no full page reload)
  - [ ] Verify csrf_token hidden field exists with NEW value
  - [ ] Submit again (with another wrong password)
  - [ ] Verify token rotates again
  - [ ] **Result**: PASS / FAIL

  ### HTMX Preserves Auth Cookie
  - [ ] After HTMX swap above, check DevTools → Application → Cookies
  - [ ] Verify access_token cookie still exists (not cleared by HTMX)
  - [ ] Verify csrf_token cookie updated
  - [ ] Navigate to /dashboard
  - [ ] Verify still logged in (auth preserved)
  - [ ] **Result**: PASS / FAIL

  ---

  ## Summary

  **Tests Executed**: _____ / 15
  **Tests Passed**: _____
  **Tests Failed**: _____
  **Critical Failures**: _____ (Test 2 Garmin attack must PASS)

  **Overall Status**: PASS / FAIL

  **Issues Found**:
  1. ___________________________________________
  2. ___________________________________________

  **Action Items**:
  1. ___________________________________________
  2. ___________________________________________

  **Sign-off**:
  - Tester: _____________________ Date: __________
  - Reviewer: ___________________ Date: __________
  ```

- [ ] Execute manual runsheet (fill in results)

- [ ] Document any issues found

- [ ] Commit runsheet:
  ```bash
  git add docs/development/csrf/MANUAL_TESTING_RUNSHEET.md
  git commit -m "docs: add CSRF protection manual testing runsheet"
  ```

**Success Criteria**:
- [ ] Runsheet created with comprehensive test cases
- [ ] All 15 test scenarios defined
- [ ] Runsheet executed (can be partial if blocked)
- [ ] Results documented (PASS/FAIL for each test)
- [ ] Critical Test 2 (Garmin attack) PASSED

**Reference**: Spec lines 1160-1200

**Time Estimate**: 25 minutes (10 min create, 15 min execute)

---

### Test Verification

**Goal**: Verify all Phase 3 E2E tests pass

- [ ] Run all E2E CSRF tests:
  ```bash
  # Ensure local-e2e-server.sh running in another terminal
  uv --directory backend run pytest tests/e2e_playwright/test_csrf_protection.py -v
  ```

- [ ] Run full E2E test suite (regression check):
  ```bash
  uv --directory backend run pytest tests/e2e_playwright -v
  ```

- [ ] Verify all tests pass (no regressions):
  ```bash
  # All tests (unit + integration + e2e)
  uv --directory backend run pytest tests/ -v --cov=app --cov-report=term-missing
  ```

**Success Criteria**:
- [ ] All 5 new CSRF E2E tests pass
- [ ] All existing E2E tests still pass (no regressions)
- [ ] Total test execution time < 2 minutes for E2E CSRF tests
- [ ] Overall coverage ≥ 80%

**Time Estimate**: 5 minutes

---

### Security Validation

**Goal**: Final security scan and validation

- [ ] Run security scanner:
  ```bash
  uv run bandit -c backend/pyproject.toml -r backend/app/ -ll
  ```

- [ ] Verify no CSRF-related security warnings

- [ ] Check for common CSRF pitfalls:
  - [ ] All POST routes have `csrf_protect.validate_csrf(request)`
  - [ ] CSRF validation happens BEFORE business logic
  - [ ] All error responses rotate tokens
  - [ ] All forms include `<input name="csrf_token">`

- [ ] Verify OWASP CSRF Prevention Cheat Sheet compliance:
  - [ ] Double Submit Cookie pattern implemented
  - [ ] Tokens have sufficient entropy (32+ chars)
  - [ ] Tokens expire (1 hour max_age)
  - [ ] SameSite=Strict for CSRF cookie
  - [ ] Generic error messages (no information leakage)

**Success Criteria**:
- [ ] Bandit scan passes with 0 issues
- [ ] All POST routes protected (verified via grep)
- [ ] OWASP checklist 5/5 items complete

**Time Estimate**: 10 minutes

---

### Code Quality Checks

**Goal**: Final quality verification

- [ ] Run linter:
  ```bash
  uv run ruff check .
  ```

- [ ] Run formatter:
  ```bash
  uv run ruff format .
  ```

- [ ] Verify no regressions in existing code

**Success Criteria**:
- [ ] Ruff passes cleanly
- [ ] Code formatted consistently
- [ ] No new warnings or errors

**Time Estimate**: 5 minutes

---

### Git Workflow

**Goal**: Push branch and create PR into feat/csrf

- [ ] Final commit with phase completion:
  ```bash
  git add .
  git commit -m "docs: Mark Phase 3 complete in plan"
  ```

- [ ] Push phase branch:
  ```bash
  git push -u origin feat/csrf-phase-3
  ```

- [ ] Create PR into feat/csrf:
  ```bash
  gh pr create --base feat/csrf --title "Phase 3: E2E Tests & Security Validation" \
    --body "Adds comprehensive E2E tests and security validation for CSRF protection.

  **Changes**:
  - E2E test: Cross-origin POST attack blocked (Garmin + Register)
  - E2E test: Token rotation on validation errors
  - E2E test: HTMX partial updates preserve tokens
  - Manual testing runsheet (15 test scenarios)
  - Security validation (bandit + OWASP checklist)

  **Testing**:
  - 5 new E2E tests (all passing)
  - Manual runsheet executed (15/15 scenarios)
  - Security scan: 0 issues
  - Coverage: XX% (≥80% target)

  **Validation**:
  - CRITICAL: Garmin link attack BLOCKED (manual test passed)
  - Token rotation verified in browser
  - HTMX compatibility confirmed
  - All routes protected (grep verified)

  **Closes**: #8 (CSRF protection complete)"
  ```

- [ ] Update this plan: Mark all steps ✅ DONE
- [ ] Update ROADMAP.md: Phase 3 status → ✅ DONE, overall feature → ✅ COMPLETE

**Success Criteria**:
- [ ] PR created targeting feat/csrf branch
- [ ] PR description highlights security validation
- [ ] CI checks passing on PR
- [ ] Phase 3 plan marked complete

**Time Estimate**: 5 minutes

---

## Success Criteria

### Technical Success

- [ ] 5 E2E tests passing (attack prevention, token rotation, HTMX compatibility)
- [ ] Manual runsheet completed (15/15 scenarios documented)
- [ ] All existing E2E tests still pass (no regressions)
- [ ] Security scan passes (bandit 0 issues)

### Security Validation

- [ ] **CRITICAL**: Cross-origin POST attack blocked (E2E test + manual)
- [ ] **CRITICAL**: Garmin link attack prevention verified manually
- [ ] Token rotation works on all error paths (E2E verified)
- [ ] HTMX partial updates preserve CSRF protection (E2E verified)
- [ ] OWASP CSRF Prevention checklist complete (5/5)

### Quality Metrics

- [ ] E2E test coverage for all CSRF user journeys
- [ ] All quality gates pass (ruff, bandit, tests)
- [ ] No regressions in existing functionality
- [ ] Manual testing provides regression baseline

---

## Notes

### Design Decisions

- **E2E tests focus on critical paths**: Attack prevention and token rotation are highest priority
- **Manual testing complements automation**: Some scenarios easier to verify manually (attack HTML files)
- **HTMX compatibility is crucial**: Partial DOM updates common in Selflytics, must preserve CSRF tokens
- **Runsheet provides regression baseline**: Future changes can re-run manual tests to catch regressions

### Specification References

- Lines 655-729: User Journey 2 - CSRF Attack Blocked (Garmin Link) - **PRIMARY TEST SCENARIO**
- Lines 733-799: User Journey 3 - Form Validation Error (Token Refresh)
- Lines 1075-1157: E2E Tests (Playwright specifications)
- Lines 1160-1200: Manual Testing Checklist

### E2E Test Structure

```
test_csrf_protection.py (5 tests, ~60 lines each):
├── test_csrf_blocks_cross_origin_garmin_link_attack (HIGH PRIORITY)
├── test_csrf_blocks_cross_origin_register_attack
├── test_csrf_token_rotation_on_validation_error
├── test_csrf_token_rotation_on_login_failure
└── test_csrf_token_works_with_htmx_partial_updates
```

### Common Pitfalls

- **Firestore emulator required**: E2E tests will fail without emulator running
- **Playwright browsers**: Ensure `playwright install chromium` run before first E2E test
- **Async timing**: Use `wait_for_timeout()` after HTMX submissions to allow fragment swap
- **Attack HTML files**: Must be served from different origin (file:// protocol works for testing)

### OWASP CSRF Prevention Compliance

✅ **Token-based mitigation**: Double Submit Cookie pattern
✅ **Sufficient randomness**: 32+ character URL-safe tokens
✅ **Token expiration**: 1-hour max_age prevents stale token reuse
✅ **SameSite protection**: csrf_token cookie uses SameSite=Strict
✅ **User interaction**: All state-changing operations require POST with token

---

## Dependencies for Final Merge

**Final PR to main needs from Phase 3**:
- [ ] All E2E tests passing
- [ ] Manual testing runsheet complete
- [ ] Security validation complete (bandit + OWASP)
- [ ] No regressions in existing tests
- [ ] Documentation updated (ROADMAP, phase plans)

With Phase 3 complete, the CSRF protection feature is production-ready for merge to main.

---

## Session Progress Summary

**Session 1**:
- [ ] Steps 1-4: E2E tests and manual runsheet
- [ ] All tests passing
- [ ] Security validation complete
- [ ] Feature fully validated

**Final Status**: [ ] COMPLETE / [ ] IN PROGRESS / [ ] BLOCKED

---

*Last Updated: 2025-11-15*
*Status: PLANNED*
