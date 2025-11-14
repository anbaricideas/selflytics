# Manual Testing Runsheet - User Journeys

**Purpose**: Validate complete user flows work end-to-end with real user interactions

**Prerequisites**:
- [ ] Local e2e server running: `./scripts/local-e2e-server.sh`
- [ ] Browser open to http://localhost:8042
- [ ] Note: Use unique email for each test run (append timestamp)

---

## Journey 1: New User Registration → Garmin Linking

**Scenario**: First-time user signs up and connects Garmin account

### 1. Navigate to Home
- [ ] Open http://localhost:8042
- [ ] Verify redirected to /login
- [ ] Verify login form visible with email and password fields

### 2. Navigate to Registration
- [ ] Click "Register" link
- [ ] Verify redirected to /register
- [ ] Verify registration form visible with 4 fields:
  - Display Name
  - Email
  - Password
  - Confirm Password

### 3. Fill Registration Form
- [ ] Enter Display Name: "Manual Test User"
- [ ] Enter Email: `test-manual-{TIMESTAMP}@example.com` (use actual timestamp)
- [ ] Enter Password: "TestPass123!"
- [ ] Enter Confirm Password: "TestPass123!"
- [ ] Verify password fields are masked (showing dots/asterisks)

### 4. Submit Registration
- [ ] Click "Create Account" button
- [ ] Verify button shows loading state ("Creating Account..." with spinner)
- [ ] Verify redirected to /dashboard
- [ ] Verify welcome message displays: "Welcome back, Manual Test User!"

### 5. Check Garmin Status (Dashboard)
- [ ] Verify banner shows: "Connect Your Garmin Account"
- [ ] Verify "Connect Now" or similar button visible

### 6. Navigate to Garmin Settings
- [ ] Click Garmin connection button
- [ ] Verify redirected to /garmin/link or /settings/garmin
- [ ] Verify form shows: "Link Your Garmin Account"
- [ ] Verify form has username and password fields

### 7. Link Garmin Account ⚠️ REQUIRES REAL CREDENTIALS
> **Note**: Manual testing hits the real Garmin API (not mocked). You have two options:
> - **Option A (Recommended)**: SKIP this step - Garmin linking is thoroughly tested in e2e tests with mocked API
> - **Option B**: Use your own real Garmin account credentials to test the full flow

**If using real credentials (Option B)**:
- [ ] Enter your real Garmin Connect email
- [ ] Enter your real Garmin Connect password
- [ ] Click "Link Account" button
- [ ] Verify button shows loading state ("Linking..." with spinner)
- [ ] Verify success message appears: "Garmin account linked"
- [ ] Verify form is replaced with success status (HTMX swap - no full page reload)
- [ ] Verify "Sync Now" button appears

**If skipping (Option A)**:
- [ ] SKIPPED - Garmin linking tested in automated e2e tests

### 8. Manual Sync (only if linked in step 7)
- [ ] Click "Sync Now" button (if Garmin linked)
- [ ] Verify loading indicator appears
- [ ] Verify success message: "Sync completed successfully"
- [ ] Verify recent activities appear (if using real Garmin account)

**Expected Result**: ✅ User registered, logged in, linked Garmin, and synced data successfully

---

## Journey 2: Returning User Login → Chat

**Scenario**: Existing user logs in and interacts with chat

### 1. Logout (if still logged in)
- [ ] Click logout button in navigation
- [ ] Verify redirected to /login

### 2. Login with Existing Credentials
- [ ] Navigate to /login
- [ ] Enter email from Journey 1
- [ ] Enter password: "TestPass123!"
- [ ] Click "Login" button
- [ ] Verify button shows loading state
- [ ] Verify redirected to /dashboard
- [ ] Verify welcome message shows correct name

### 3. Navigate to Chat (if available)
- [ ] Look for "Chat" or "Chat Analysis" link/card
- [ ] Click to navigate to chat interface
- [ ] Verify chat interface loads with:
  - Message input field
  - Send button
  - Messages area (empty or with history)

### 4. Start New Conversation (if chat available)
- [ ] Click "New Chat" button (if exists)
- [ ] Verify messages area clears
- [ ] Verify input field is focused and ready

### 5. Send Message
- [ ] Type: "How am I doing?"
- [ ] Click "Send" button or press Enter
- [ ] Verify user message appears (right side, blue/colored)
- [ ] Verify loading indicator ("AI is thinking...")
- [ ] Verify AI response appears (left side, gray)
- [ ] Verify conversation updates in sidebar (if sidebar exists)

### 6. Continue Conversation
- [ ] Type: "Show me my recent activities"
- [ ] Press Enter key (test keyboard submission)
- [ ] Verify message sent successfully
- [ ] Verify AI responds

**Expected Result**: ✅ User logged in and successfully interacted with chat

**Note**: If chat is not yet implemented, mark this journey as SKIPPED

---

## Journey 3: Error Handling & Recovery

**Scenario**: User encounters various errors and recovers gracefully

### 1. Registration with Mismatched Passwords
- [ ] Logout (if logged in)
- [ ] Navigate to /register
- [ ] Enter Display Name: "Error Test"
- [ ] Enter Email: `error-test-{TIMESTAMP}@example.com`
- [ ] Enter Password: "TestPass123!"
- [ ] Enter Confirm Password: "DifferentPass456!"
- [ ] Click "Create Account"
- [ ] Verify error message appears: "Passwords do not match" or similar
- [ ] Verify error is displayed inline (red text)
- [ ] Verify form is still editable (not cleared)

### 2. Registration with Duplicate Email
- [ ] Correct the confirm password field
- [ ] Change email to one used in Journey 1
- [ ] Click "Create Account"
- [ ] Verify server error message: "Email already registered"
- [ ] Verify error displayed via HTMX swap (no full page reload)
- [ ] Verify form remains visible and editable

### 3. Login with Wrong Password
- [ ] Navigate to /login
- [ ] Enter valid email from Journey 1
- [ ] Enter wrong password: "WrongPassword123!"
- [ ] Click "Login"
- [ ] Verify error message: "Incorrect email or password" or similar
- [ ] Verify error is red and clearly visible
- [ ] Verify form still visible (can retry)

### 4. Login with Correct Password (Recovery)
- [ ] Enter correct password: "TestPass123!"
- [ ] Click "Login"
- [ ] Verify successful login to dashboard
- [ ] Verify error message is gone

### 5. Garmin Link with Invalid Credentials ⚠️ OPTIONAL (requires real Garmin account)
> **Note**: This test requires a real Garmin account. If you don't have one, SKIP to step 6.

- [ ] Navigate to /garmin/link or /settings/garmin
- [ ] If already linked, skip this section
- [ ] Enter: "wrong@garmin.com" (or any invalid email)
- [ ] Enter: "wrongpassword"
- [ ] Click "Link Account"
- [ ] Verify error message appears (HTMX swap)
- [ ] Verify error mentions invalid credentials or similar
- [ ] Verify form remains visible for retry

### 6. Retry with Valid Credentials ⚠️ OPTIONAL
> **Note**: Only if you're testing with a real Garmin account

- [ ] Enter your real Garmin email
- [ ] Enter your real Garmin password
- [ ] Click "Link Account"
- [ ] Verify success message
- [ ] Verify error message is gone
- [ ] Verify "Sync Now" button appears

**OR if skipping Garmin tests**:
- [ ] SKIPPED - Garmin error handling tested in automated e2e tests

**Expected Result**: ✅ All errors displayed clearly, user able to recover without page refreshes

---

## Journey 4: Accessibility & Keyboard Navigation

**Scenario**: User navigates entirely with keyboard and verifies accessibility

### 1. Tab Navigation (Registration Page)
- [ ] Navigate to /register
- [ ] Press Tab key repeatedly
- [ ] Verify focus order:
  1. Display Name input
  2. Email input
  3. Password input
  4. Confirm Password input
  5. Submit button
  6. Login link
- [ ] Verify focus outlines are clearly visible
- [ ] Verify no keyboard traps (can navigate through all elements)

### 2. Keyboard Form Submission
- [ ] Fill display name field
- [ ] Press Tab to move to next field
- [ ] Fill email field
- [ ] Press Tab to move to password
- [ ] Fill password field
- [ ] Press Tab to confirm password
- [ ] Fill confirm password field
- [ ] Press Enter key (not Tab to button)
- [ ] Verify form submits successfully
- [ ] Verify no button click needed

### 3. Visual Focus Indicators
- [ ] Navigate to /login page
- [ ] Use Tab to move through form
- [ ] Verify every focusable element shows clear outline
- [ ] Verify outline color is high contrast (not gray on gray)
- [ ] Verify outline appears on:
  - Input fields
  - Buttons
  - Links

### 4. Screen Reader Check (Optional)
- [ ] Enable screen reader:
  - macOS: VoiceOver (Cmd+F5)
  - Windows: NVDA (free download)
- [ ] Navigate to registration form
- [ ] Verify labels are announced for each field
- [ ] Verify required fields are announced
- [ ] Trigger validation error
- [ ] Verify error message is announced (aria-live)

**Expected Result**: ✅ Full keyboard navigation works, focus indicators visible, accessible to assistive tech

---

## Journey 5: HTMX Partial Updates (No Full Page Reloads)

**Scenario**: Verify HTMX interactions don't cause full page reloads

### 1. Monitor Network Tab
- [ ] Open browser DevTools (F12)
- [ ] Go to Network tab
- [ ] Check "Preserve log"

### 2. Registration with HTMX
- [ ] Navigate to /register
- [ ] Fill form with valid data
- [ ] Click "Create Account"
- [ ] Check Network tab
- [ ] Verify: POST request to /auth/register
- [ ] Verify: Response has HX-Redirect header (not 302 redirect)
- [ ] Verify: Page navigates to /dashboard without full reload indicator

### 3. Login Form Submission
- [ ] Logout and return to /login
- [ ] Fill form with valid credentials
- [ ] Click "Login"
- [ ] Check Network tab
- [ ] Verify: POST request to /auth/login
- [ ] Verify: HX-Redirect header present
- [ ] Verify: No full document reload (no white flash)

### 4. Garmin Link Form (HTMX Swap)
- [ ] Navigate to /garmin/link (if not already linked, use new test user)
- [ ] Clear Network log
- [ ] Enter mock credentials
- [ ] Click "Link Account"
- [ ] Verify in Network tab:
  - POST request to /garmin/link
  - Response is HTML fragment (not full page)
  - Response has data-testid="garmin-status-linked"
- [ ] Verify: Form element is replaced with success message (no page reload)
- [ ] Verify: URL did NOT change
- [ ] Verify: No white flash or scroll jump

### 5. Garmin Sync Button
- [ ] Click "Sync Now" button
- [ ] Verify in Network tab:
  - POST request to /garmin/sync
  - Response is HTML fragment
- [ ] Verify: Success message appears via HTMX swap
- [ ] Verify: No full page reload

**Expected Result**: ✅ All form submissions use HTMX, no full page reloads observed

---

## Post-Journey Verification

### Database State (Firestore Emulator)
- [ ] Open http://localhost:4000 (Firestore Emulator UI - if running)
- [ ] Navigate to Firestore tab
- [ ] Check `users` collection:
  - [ ] Verify test users exist with correct emails
  - [ ] Verify passwords are hashed (not plaintext)
- [ ] Check `garmin_tokens` collection (if exists):
  - [ ] Verify token entries for linked users
  - [ ] Verify tokens are encrypted (not plaintext)

### Cleanup
- [ ] Stop local-e2e-server.sh (Ctrl+C in terminal)
- [ ] Emulator data automatically cleared on restart (ephemeral)

---

## Sign-Off

**Tester**: Bryn (with Claude Code)
**Date**: 2025-11-14
**Environment**: Local (http://localhost:8042)
**All Journeys Passed**: ☐ Yes  ☑ No (7 bugs found)

**Journeys Completed**:
- [x] Journey 1: New User Registration → Garmin Linking (✅ partial - registration works, Garmin blocked by bugs)
- [x] Journey 2: Returning User Login → Chat (✅ partial - login works, chat not linked, API key issue)
- [x] Journey 3: Error Handling & Recovery (⚠️ validation works but UX bugs)
- [x] Journey 4: Accessibility & Keyboard Navigation (✅ excellent - full keyboard support)
- [x] Journey 5: HTMX Partial Updates (✅ HTMX working, but response fragments cause nesting)

**Issues Found (CRITICAL)**:
1. **Login button stuck after 401** - Loading state not reset on error, blocks retry (CRITICAL UX)
2. **Garmin link returns 401** - Mock credentials fail, unexpected authentication error
3. **Nested/duplicate forms in error responses** - HTMX swaps full container causing duplication (Garmin, Registration)
4. **Logout returns 404** - Logout works but shows error page instead of redirecting to /login
5. **Chat not linked from dashboard** - Card says "Coming in Phase 3" but chat exists at /chat
6. **Chat OpenAI API key invalid** - .env.local has "test-key" which fails API validation
7. **Chat page layout** - Need to scroll to see message input field

**HTMX Observations**:
- ✅ HX-Redirect working correctly for registration/login (no full page reloads)
- ✅ Partial swaps working (fragments returned, not full HTML pages)
- ⚠️ Error response fragments include full container (`<div class="bg-white border...">`) causing nested forms when swapped

**Notes**:
- Registration flow works perfectly (except password mismatch shows nested form)
- Keyboard accessibility is excellent (tab order, focus indicators, Enter submission)
- Core user journeys are functional but error handling UX needs improvement
- Most bugs are HTMX error response formatting issues (systematic problem across endpoints)
- Recommend fixing Bug #1 (login stuck), #3 (nested forms), and #5 (chat link) as highest priority

---

**Next Steps After Completion**:
- Fix any critical issues found
- Document non-critical issues as GitHub issues
- Mark Phase 4 as complete in ROADMAP.md
