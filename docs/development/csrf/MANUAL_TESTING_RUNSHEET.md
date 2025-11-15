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
- [ ] Test user account created (email: test-user@example.com, password: TestPass123!)

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
  - **Token 1**: ___________________________________________ (e.g., eyJhbGc6IkpXVCJ9.dGVzdA.SflKxwRJ... - yours will differ)
- [ ] Fill form with password MISMATCH:
  - Email: rotation-test@example.com
  - Display Name: Rotate Test
  - Password: Pass123!
  - Confirm Password: Pass456!  ← MISMATCH
- [ ] Submit form
- [ ] Verify error: "Passwords do not match"
- [ ] Copy NEW csrf_token value from hidden field
  - **Token 2**: ___________________________________________ (e.g., eyJhbGc6IkpXVCJ9.bmV3dG9rZW4.abc123... - yours will differ)
- [ ] Verify Token 2 ≠ Token 1 (rotation occurred)
- [ ] Open DevTools → Network → Find POST request
- [ ] Verify response includes `Set-Cookie: csrf_token=...` (new cookie)
- [ ] Correct password to Pass123 and submit
- [ ] Verify successful registration
- [ ] **Result**: PASS / FAIL

### Login Invalid Credentials
- [ ] Navigate to http://localhost:8000/login
- [ ] Copy csrf_token value
  - **Token 1**: ___________________________________________ (e.g., eyJhbGc6IkpXVCJ9.dGVzdA.SflKxwRJ... - yours will differ)
- [ ] Enter: test-user@example.com / WrongPassword
- [ ] Submit form
- [ ] Verify error: "Incorrect email or password"
- [ ] Copy NEW csrf_token value
  - **Token 2**: ___________________________________________ (e.g., eyJhbGc6IkpXVCJ9.bmV3dG9rZW4.abc123... - yours will differ)
- [ ] Verify Token 2 ≠ Token 1
- [ ] Enter correct password and submit
- [ ] Verify successful login
- [ ] **Result**: PASS / FAIL

---

## Test 5: Verify HTMX Compatibility

**Goal**: Confirm CSRF tokens work with HTMX partial DOM updates

### HTMX Form Swap (Registration)
- [ ] Navigate to http://localhost:8000/register
- [ ] Open DevTools → Network tab
- [ ] Clear network log
- [ ] Submit form with password mismatch
- [ ] In Network tab, find POST to /auth/register
- [ ] Verify response is HTML fragment (not full page)
- [ ] Verify response includes `Set-Cookie: csrf_token=...`
- [ ] Verify form re-rendered with error (no full page reload)
- [ ] Verify csrf_token hidden field exists with NEW value
- [ ] Submit again (with corrected password)
- [ ] Verify successful registration
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

---

*Reference: docs/development/csrf/CSRF_SPECIFICATION.md*
*Last Updated: 2025-11-15*
