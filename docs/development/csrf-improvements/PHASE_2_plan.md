# Phase 2: Protect Chat Send Endpoint

**Branch**: `chore/csrf-improvements-phase-2`
**Status**: NOT STARTED
**Estimated Time**: 1.5 hours

---

## Goal

Add CSRF protection to the `/chat/send` endpoint to prevent message injection, resource consumption, and potential information leakage attacks. This phase implements header-based CSRF protection for JavaScript-initiated requests.

---

## Prerequisites

- [ ] Phase 1 completed (logout protection)
- [ ] GET `/chat/` endpoint generates CSRF tokens (from Phase 1)
- [ ] CSRF cookie configuration verified (httponly=false from Phase 1)
- [ ] Current branch is `chore/csrf-improvements`

---

## Deliverables

### Backend Changes
- Updated `/chat/send` endpoint in `backend/app/routes/chat.py` with CSRF validation
- User-friendly error handling for CSRF failures

### Frontend Changes
- JavaScript helper function to read CSRF token from cookie
- Updated fetch call to include `X-CSRF-Token` header
- Error handling for missing/expired tokens with auto-refresh

### Tests
- Integration tests for chat/send CSRF protection
- E2E tests for critical security scenarios
- Manual testing verification

---

## Implementation Steps

### Setup

- [ ] ⏳ NEXT: Create branch from `chore/csrf-improvements`
  ```bash
  git checkout chore/csrf-improvements
  git pull origin chore/csrf-improvements
  git checkout -b chore/csrf-improvements-phase-2
  ```

---

### Step 1: Write Integration Tests for Chat Send CSRF (TDD - Test First)

**File**: `backend/tests/integration/test_csrf_routes.py`

**Reference**: Specification lines 801-889

#### Test 1: Chat send requires CSRF token

- [ ] Write test: `test_chat_send_requires_csrf_token`
  - Use authenticated_client fixture
  - POST `/chat/send` with valid JSON body but NO X-CSRF-Token header
  - Assert: response.status_code == 403
  - Assert: Response contains error detail about CSRF validation

#### Test 2: Chat send with valid CSRF token succeeds

- [ ] Write test: `test_chat_send_with_valid_csrf_token`
  - Use authenticated_client fixture
  - GET `/chat/` to obtain CSRF cookie
  - Extract CSRF token from cookie
  - POST `/chat/send` with:
    - Valid JSON body (message + conversation_id)
    - X-CSRF-Token header with token value
    - Cookie with same token value
  - Assert: response.status_code == 200
  - Assert: Response contains conversation_id and response fields

#### Test 3: Chat send with invalid token fails

- [ ] Write test: `test_chat_send_with_invalid_csrf_token`
  - Use authenticated_client fixture
  - GET `/chat/` to obtain legitimate token
  - POST `/chat/send` with:
    - Valid JSON body
    - X-CSRF-Token header with INVALID token ("fake_invalid_token")
    - Cookie with legitimate token
  - Assert: response.status_code == 403

#### Test 4: Chat send validates header not form field

- [ ] Write test: `test_chat_send_uses_header_not_form_field`
  - Use authenticated_client fixture
  - GET `/chat/` to obtain token
  - POST `/chat/send` with:
    - JSON body containing csrf_token field (wrong pattern)
    - NO X-CSRF-Token header
    - Cookie with token
  - Assert: response.status_code == 403 (header is required, not form field)

#### Verify Tests Fail

- [ ] Run integration tests (should FAIL - no implementation yet)
  ```bash
  uv --directory backend run pytest tests/integration/test_csrf_routes.py::test_chat_send_requires_csrf_token -v
  uv --directory backend run pytest tests/integration/test_csrf_routes.py::test_chat_send_with_valid_csrf_token -v
  uv --directory backend run pytest tests/integration/test_csrf_routes.py::test_chat_send_with_invalid_csrf_token -v
  uv --directory backend run pytest tests/integration/test_csrf_routes.py::test_chat_send_uses_header_not_form_field -v
  ```
- [ ] Verify all 4 tests fail with expected errors (no CSRF validation yet)

#### Commit

- [ ] Commit tests
  ```bash
  git add backend/tests/integration/test_csrf_routes.py
  git commit -m "test: Add integration tests for chat send CSRF protection

- Test chat send requires CSRF token (403 without header)
- Test chat send succeeds with valid token in header
- Test chat send fails with invalid token
- Test chat send validates header not form field

Tests currently fail - implementation in next commit"
  ```

---

### Step 2: Update Backend /chat/send Endpoint (TDD - Implementation)

**File**: `backend/app/routes/chat.py`

**Reference**: Specification lines 452-485

#### Update imports

- [ ] Add required imports at top of file:
  ```python
  from fastapi_csrf_protect.flexible import CsrfProtect
  from fastapi_csrf_protect.exceptions import CsrfProtectError
  ```

#### Update /chat/send endpoint

- [ ] Locate `@router.post("/send")` function (line ~28)
- [ ] Add CSRF dependencies to function signature:
  ```python
  @router.post("/send")
  async def send_message(
      request: Request,
      chat_request: ChatRequest,
      current_user: UserResponse = Depends(get_current_user),
      csrf_protect: CsrfProtect = Depends(),
  ) -> dict[str, Any]:
  ```
- [ ] Add CSRF validation with user-friendly error handling:
  ```python
  """Send chat message and get AI response.

  CSRF protection prevents attackers from sending messages on behalf of users.
  Uses X-CSRF-Token header (not form field) since this is a JSON API.
  """
  # Validate CSRF token from header with user-friendly error message
  try:
      await csrf_protect.validate_csrf(request)
  except CsrfProtectError as e:
      raise HTTPException(
          status_code=status.HTTP_403_FORBIDDEN,
          detail="Security validation failed. Please refresh the page and try again.",
      ) from e

  service = ChatService()

  try:
      response, conversation_id = await service.send_message(
          user_id=current_user.user_id, request=chat_request
      )

      return {"conversation_id": conversation_id, "response": response.model_dump()}

  except Exception as e:
      raise HTTPException(
          status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
      ) from e
  ```

#### Verify Integration Tests Pass

- [ ] Run integration tests for chat send (should now PASS)
  ```bash
  uv --directory backend run pytest tests/integration/test_csrf_routes.py -k chat_send -v
  ```
- [ ] Verify all 4 chat send tests pass

**Note**: Tests should pass because header-based validation is implemented. Frontend JavaScript will be added next.

#### Commit

- [ ] Commit backend changes
  ```bash
  git add backend/app/routes/chat.py
  git commit -m "feat: Add CSRF protection to chat send endpoint

- Add CSRF validation to POST /chat/send endpoint
- Use header-based validation (X-CSRF-Token)
- User-friendly error message for CSRF failures
- Prevents message injection and resource abuse attacks

Ref: SPECIFICATION.md lines 452-485"
  ```

---

### Step 3: Update Frontend JavaScript (TDD - Implementation)

**File**: `backend/app/templates/chat.html`

**Reference**: Specification lines 489-562

#### Add helper function to read CSRF token

- [ ] Locate the Alpine.js `chatInterface()` function (line ~180)
- [ ] Add `getCsrfToken()` helper method:
  ```javascript
  function chatInterface() {
      return {
          // ... existing properties (messages, loading, error, etc.) ...

          // Helper: Get CSRF token from cookie
          getCsrfToken() {
              const name = 'fastapi-csrf-token';
              const value = `; ${document.cookie}`;
              const parts = value.split(`; ${name}=`);
              if (parts.length === 2) return parts.pop().split(';').shift();
              return null;
          },

          // ... rest of methods ...
      };
  }
  ```

#### Update sendMessage() to include CSRF header

- [ ] Locate `sendMessage()` function (line ~220)
- [ ] Add CSRF token check before fetch:
  ```javascript
  async sendMessage() {
      if (!this.messageInput.trim()) return;

      const userMessage = this.messageInput;
      this.messageInput = '';
      this.loading = true;
      this.error = null;

      // Add user message to display immediately
      this.messages.push({
          role: 'user',
          content: userMessage,
          timestamp: new Date().toISOString()
      });

      try {
          // Get CSRF token from cookie
          const csrfToken = this.getCsrfToken();

          // Handle missing CSRF token (expired or not set)
          if (!csrfToken) {
              this.error = 'Security token expired. Please refresh the page.';
              return;
          }

          const response = await fetch('/chat/send', {
              method: 'POST',
              headers: {
                  'Content-Type': 'application/json',
                  'X-CSRF-Token': csrfToken  // Add CSRF header
              },
              body: JSON.stringify({
                  message: userMessage,
                  conversation_id: this.currentConversationId
              })
          });

          if (!response.ok) {
              const errorData = await response.json();

              // Handle CSRF token expiration gracefully
              if (response.status === 403) {
                  this.error = 'Your session has expired. Refreshing page...';
                  setTimeout(() => window.location.reload(), 2000);
                  return;
              }

              throw new Error(errorData.detail || 'Failed to send message');
          }

          const data = await response.json();

          // Store conversation ID for future messages
          if (data.conversation_id) {
              this.currentConversationId = data.conversation_id;
          }

          // Add AI response to messages
          this.messages.push(data.response);

          // Scroll to bottom
          this.$nextTick(() => {
              const container = document.getElementById('messages-container');
              if (container) {
                  container.scrollTop = container.scrollHeight;
              }
          });

      } catch (e) {
          console.error('Error sending message:', e);
          this.error = e.message || 'Failed to send message';
      } finally {
          this.loading = false;
      }
  }
  ```

#### Verify JavaScript Syntax

- [ ] Check for syntax errors:
  ```bash
  # Look for obvious issues in template
  cat /Users/bryn/repos/selflytics/backend/app/templates/chat.html | grep -A50 "getCsrfToken"
  ```
- [ ] Verify closing braces match
- [ ] Verify string quotes are properly escaped

#### Commit

- [ ] Commit frontend changes
  ```bash
  git add backend/app/templates/chat.html
  git commit -m "feat: Add CSRF token to chat send requests

- Add getCsrfToken() helper to read token from cookie
- Include X-CSRF-Token header in fetch requests
- Handle missing token with clear error message
- Auto-refresh page on 403 (expired token)
- Graceful degradation for token expiration

Completes chat send CSRF protection implementation"
  ```

---

### Step 4: Write E2E Tests for Critical Security Scenarios

**File**: `backend/tests/e2e_playwright/test_csrf_protection.py`

**Reference**: Specification lines 933-1007

#### Test 1: Chat send includes CSRF token header

- [ ] Write test: `test_chat_send_includes_csrf_token_header`
  - Navigate to chat page (authenticated)
  - Set up request interception to capture /chat/send requests
  - Send a chat message via UI
  - Assert: Request includes X-CSRF-Token header
  - Assert: Header value is non-empty

#### Test 2: Legitimate chat message works end-to-end

- [ ] Write test: `test_legitimate_chat_message_with_csrf`
  - Navigate to chat page (authenticated)
  - Type message in input field
  - Click send button
  - Wait for AI response to appear
  - Assert: Message sent successfully
  - Assert: No error messages shown

#### Test 3: Cross-origin chat attack blocked

- [ ] Write test: `test_cross_origin_chat_attack_blocked`
  - Login to get authenticated session
  - Create malicious HTML page with JavaScript fetch to /chat/send
  - Navigate to malicious page (simulates user clicking phishing link)
  - Wait for fetch attempt
  - Navigate back to chat to verify no unwanted messages
  - Assert: Attacker's message NOT in chat history

#### Verify E2E Tests Pass

- [ ] Start local E2E environment:
  ```bash
  ./scripts/local-e2e-server.sh
  ```
- [ ] In another terminal, run E2E tests:
  ```bash
  uv --directory backend run pytest tests/e2e_playwright/test_csrf_protection.py -v --headed
  ```
- [ ] Verify all E2E tests pass

**Note**: If tests fail, use `--headed` mode to see browser and debug JavaScript errors.

#### Commit

- [ ] Commit E2E tests
  ```bash
  git add backend/tests/e2e_playwright/test_csrf_protection.py
  git commit -m "test: Add E2E tests for chat CSRF protection

- Test chat requests include X-CSRF-Token header
- Test legitimate chat message works end-to-end
- Test cross-origin attack is blocked
- Verifies JavaScript token handling in real browser"
  ```

---

### Step 5: Run Full Test Suite

**Goal**: Ensure no regressions in existing functionality

- [ ] Stop local-e2e-server.sh if still running
- [ ] Run all tests
  ```bash
  uv --directory backend run pytest tests/ -v --cov=app
  ```
- [ ] Verify:
  - All tests pass (0 failures)
  - Coverage ≥ 80%
  - No new warnings

**If tests fail**: Debug and fix issues before proceeding.

#### Commit (if any fixes needed)

- [ ] If fixes were needed, commit them:
  ```bash
  git add <fixed-files>
  git commit -m "fix: <description of fix>"
  ```

---

### Step 6: Manual Testing Verification

**Goal**: Verify CSRF protection works in actual browser

#### Test 1: Verify CSRF token in request headers

- [ ] Start dev server: `./scripts/dev-server.sh`
- [ ] Navigate to http://localhost:8000/chat
- [ ] Open browser DevTools → Network tab
- [ ] Type a test message in chat input
- [ ] Click send button
- [ ] Find POST /chat/send request in Network tab
- [ ] Click request → Headers tab → Request Headers
- [ ] Verify: `X-CSRF-Token: <token-value>` header exists
- [ ] Verify: Token value matches cookie value
- [ ] Open DevTools → Application tab → Cookies
- [ ] Verify: `fastapi-csrf-token` cookie exists

#### Test 2: Verify legitimate chat works

- [ ] Send several chat messages
- [ ] Verify: All messages send successfully
- [ ] Verify: AI responses appear
- [ ] Verify: No error messages shown

#### Test 3: Verify missing token error handling

- [ ] Open DevTools → Console tab
- [ ] Manually delete CSRF cookie:
  ```javascript
  document.cookie = 'fastapi-csrf-token=; Max-Age=0; path=/';
  ```
- [ ] Try to send a chat message
- [ ] Verify: Error message appears: "Security token expired. Please refresh the page."
- [ ] Verify: Message NOT sent to server

#### Test 4: Verify 403 auto-refresh

- [ ] Refresh page to get new token
- [ ] Open DevTools → Console tab
- [ ] Simulate expired token by sending request with fake token:
  ```javascript
  fetch('/chat/send', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRF-Token': 'fake_expired_token'
    },
    body: JSON.stringify({message: 'test', conversation_id: null})
  })
  ```
- [ ] Verify: Request returns 403
- [ ] Verify: Error detail mentions security validation

**Note**: Auto-refresh only triggers from UI sendMessage() function, not manual fetch

#### Test 5: Verify cross-origin attack is blocked

- [ ] Create a test HTML file locally:
  ```html
  <!-- /tmp/csrf-attack-test.html -->
  <!DOCTYPE html>
  <html>
  <body>
  <h1>CSRF Attack Test</h1>
  <button onclick="attack()">Attempt Attack</button>
  <div id="result"></div>
  <script>
  async function attack() {
    try {
      const response = await fetch('http://localhost:8000/chat/send', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        credentials: 'include',  // Sends cookies
        body: JSON.stringify({
          message: 'ATTACKER MESSAGE',
          conversation_id: null
        })
        // NO X-CSRF-Token header
      });
      document.getElementById('result').innerText =
        'Status: ' + response.status + ' (Expected: 403)';
    } catch (e) {
      document.getElementById('result').innerText = 'Error: ' + e.message;
    }
  }
  </script>
  </body>
  </html>
  ```
- [ ] Open file:///tmp/csrf-attack-test.html in browser
- [ ] Click "Attempt Attack" button
- [ ] Verify: Status shows 403 (or CORS error - both are acceptable)
- [ ] Navigate to http://localhost:8000/chat
- [ ] Verify: "ATTACKER MESSAGE" NOT in chat history

#### Manual Testing Results

- [ ] Document results: _(All tests passed? Any issues?)_

---

### Step 7: Code Quality Checks

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

### Step 8: Update Phase Plan Status

- [ ] Mark all checkboxes in this plan as complete
- [ ] Update step statuses:
  - Change ⏳ NEXT markers to ✅ DONE
  - Update any session summaries or notes
- [ ] Update phase status at top of document to ✅ DONE

---

### Step 9: Final Commit and Push

- [ ] Review all changes:
  ```bash
  git log --oneline chore/csrf-improvements..HEAD
  git diff chore/csrf-improvements...HEAD
  ```
- [ ] Verify commit history is clean and descriptive
- [ ] Push to origin:
  ```bash
  git push origin chore/csrf-improvements-phase-2
  ```
- [ ] Create PR to `chore/csrf-improvements` (not main)
  - Title: "Phase 2: Protect Chat Send Endpoint"
  - Description: Reference this phase plan and spec lines 444-607
  - Link to issue #12

---

## Success Criteria

### Functional

- [x] `/chat/send` endpoint validates CSRF token from header
- [x] Chat interface JavaScript reads CSRF token from cookie
- [x] Chat interface sends X-CSRF-Token header with requests
- [x] Missing token handled gracefully with clear error message
- [x] Expired token (403) triggers auto-refresh with delay

### Testing

- [x] Integration test: chat send requires CSRF token (403 without)
- [x] Integration test: chat send succeeds with valid token in header
- [x] Integration test: chat send fails with invalid token
- [x] Integration test: header validation (not form field)
- [x] E2E test: chat requests include X-CSRF-Token header
- [x] E2E test: legitimate chat message works
- [x] E2E test: cross-origin attack blocked
- [x] Manual test: X-CSRF-Token header in Network tab
- [x] Manual test: legitimate chat works
- [x] Manual test: missing token error handling
- [x] Manual test: cross-origin attack blocked

### Quality

- [x] All tests pass (integration + E2E + existing)
- [x] Coverage ≥ 80% maintained
- [x] No type errors (mypy)
- [x] No linting errors (ruff)
- [x] No security warnings (bandit)

---

## Notes

### Design Decisions

- **Header-based CSRF**: Chat uses X-CSRF-Token header (not form field) because it's a JSON API
- **JavaScript reads cookie**: Cookie must have `httponly=false` (verified in Phase 1)
- **Graceful degradation**: Missing token shows clear message instead of generic error
- **Auto-refresh on 403**: User sees "session expired" message and page auto-reloads after 2 seconds
- **Error handling**: Both client-side (missing token check) and server-side (403 response) validation

### Spec References

- Chat send endpoint protection: Specification lines 452-485
- Frontend JavaScript changes: Specification lines 489-562
- Token expiration handling: Specification lines 571-607
- Integration tests: Specification lines 801-889
- E2E tests: Specification lines 933-1007

### Common Patterns (from existing code)

- Import: `from fastapi_csrf_protect.flexible import CsrfProtect`
- Import: `from fastapi_csrf_protect.exceptions import CsrfProtectError`
- Dependency: `csrf_protect: CsrfProtect = Depends()`
- Validation: `await csrf_protect.validate_csrf(request)`
- Header name: `X-CSRF-Token` (configured in main.py)
- Cookie name: `fastapi-csrf-token` (hardcoded by library)

### Token Expiration Flow

1. User opens chat page → GET /chat/ generates CSRF token (1h expiry)
2. User leaves tab open for 2+ hours
3. User tries to send message → JavaScript reads expired cookie
4. Server rejects with 403 → JavaScript shows "session expired" message
5. Page auto-reloads after 2 seconds → New token generated
6. User can immediately retry their message

---

## Dependencies for Next Phase

Phase 3 needs from Phase 2:
- ✅ All endpoints protected (logout + chat send)
- ✅ All tests passing (integration + E2E)
- ✅ Manual verification complete

---

**End of Phase 2 Plan**
