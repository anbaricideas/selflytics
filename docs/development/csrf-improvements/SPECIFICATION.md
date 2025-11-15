# CSRF Protection Improvements Specification

## Document Information

- **Version**: 1.0
- **Created**: 2025-11-15
- **Status**: Draft
- **Related Issues**:
  - [#12 - Integrate CSRF protection into settings page logout form](https://github.com/anbaricideas/selflytics/issues/12)
- **Parent Specification**: `docs/development/csrf/CSRF_SPECIFICATION.md`

---

## Table of Contents

1. [Overview](#overview)
2. [Security Assessment](#security-assessment)
3. [Identified Gaps](#identified-gaps)
4. [Proposed Solutions](#proposed-solutions)
5. [Implementation Plan](#implementation-plan)
6. [Testing Strategy](#testing-strategy)
7. [References](#references)

---

## Overview

### Purpose

This specification addresses CSRF protection gaps identified during a comprehensive security review of the Selflytics application. While PR #21 implemented excellent CSRF protection for most endpoints, two critical endpoints remain unprotected:

1. `POST /logout` - Settings page logout form
2. `POST /chat/send` - Chat message submission (JSON API)

### Context

**Existing CSRF Implementation** (PR #21):
- ✅ Comprehensive CSRF protection using `fastapi-csrf-protect` library
- ✅ Double Submit Cookie pattern implementation
- ✅ Protected endpoints: `/auth/register`, `/auth/login`, `/garmin/link`, `/garmin/sync`, `DELETE /garmin/link`
- ✅ Extensive test coverage (unit, integration, E2E)
- ✅ HTMX-compatible token rotation

**Security Review Findings**:
- ❌ `/logout` endpoint has no CSRF validation
- ❌ Settings page logout form has no CSRF token
- ❌ Chat page logout form has no CSRF token
- ❌ `/chat/send` endpoint has no CSRF validation
- ❌ Chat interface JavaScript sends no CSRF token

---

## Security Assessment

### Vulnerability 1: Unprotected Logout Endpoint

**Endpoint**: `POST /logout` (`backend/app/routes/auth.py:276`)

**Current Implementation**:
```python
@router.post("/logout")
async def logout() -> Response:
    """Logout user by clearing authentication cookie."""
    response = Response(status_code=status.HTTP_303_SEE_OTHER)
    response.headers["Location"] = "/login"
    response.delete_cookie(key="access_token")
    return response
```

**Risk Level**: Medium

**Attack Scenario**:
```html
<!-- Attacker's malicious site: evil.com -->
<html>
<body onload="document.forms[0].submit()">
  <form action="https://selflytics.app/logout" method="POST">
    <!-- Auto-submits when victim visits page -->
  </form>
</body>
</html>
```

**Attack Flow**:
1. Victim is logged into Selflytics (has valid `access_token` cookie)
2. Victim visits attacker's website (via phishing email, forum link, etc.)
3. Attacker's page auto-submits POST to `/logout`
4. Browser automatically sends victim's auth cookie with request
5. Selflytics backend processes request and clears cookie
6. **Result**: Victim is forcibly logged out

**Impact**:
- ⚠️ **Denial of Service**: Repeated forced logouts frustrate users
- ⚠️ **Session Disruption**: Interrupts user workflows (especially during data analysis)
- ⚠️ **Social Engineering**: Can be combined with fake login pages
- ℹ️ **Low Data Risk**: No data exfiltration or modification (only session termination)

**Mitigating Factors**:
- Logout CSRF is generally considered lower severity than other operations
- No data is modified or leaked (only cookie is cleared)
- User can simply log back in

**Why Protection is Still Needed**:
- Defense in depth: All state-changing POST endpoints should be protected
- Consistency: Other auth endpoints (`/login`, `/register`) are protected
- User experience: Prevents frustrating logout attacks
- Compliance: OWASP best practices recommend protecting all POST endpoints

---

### Vulnerability 2: Unprotected Chat Send Endpoint

**Endpoint**: `POST /chat/send` (`backend/app/routes/chat.py:28`)

**Current Implementation**:
```python
@router.post("/send")
async def send_message(
    request: ChatRequest, current_user: UserResponse = Depends(get_current_user)
) -> dict[str, Any]:
    """Send chat message and get AI response."""
    service = ChatService()
    try:
        response, conversation_id = await service.send_message(
            user_id=current_user.user_id, request=request
        )
        return {"conversation_id": conversation_id, "response": response.model_dump()}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e
```

**Risk Level**: Medium-High

**Attack Scenario**:
```html
<!-- Attacker's malicious site: evil.com -->
<html>
<body onload="attackChat()">
<script>
  async function attackChat() {
    // Send unwanted chat message on behalf of victim
    await fetch('https://selflytics.app/chat/send', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        message: 'Spam message from attacker',
        conversation_id: null
      }),
      credentials: 'include'  // Sends victim's auth cookie
    });
  }
</script>
</body>
</html>
```

**Attack Flow**:
1. Victim is logged into Selflytics
2. Victim visits attacker's website (in same browser)
3. Attacker's JavaScript sends POST to `/chat/send` with `credentials: 'include'`
4. Browser automatically sends victim's auth cookie
5. Backend creates chat message on behalf of victim
6. **Result**: Attacker can send arbitrary messages to victim's chat history

**Impact**:
- ⚠️ **Chat History Pollution**: Unwanted messages in user's conversation history
- ⚠️ **Resource Consumption**: Attacker can trigger AI requests (costs money)
- ⚠️ **Quota Exhaustion**: Could exhaust user's API limits
- ⚠️ **Privacy Violation**: Attacker could craft messages to probe for Garmin data
- ⚠️ **Potential Information Leakage**: If attacker can later access chat history
- ⚠️ **Social Engineering**: Could inject misleading AI "advice" into user's history

**Why This is More Severe Than Logout**:
- Creates persistent data (messages stored in Firestore)
- Consumes real resources (OpenAI API calls)
- Can leak information if attacker gains access later
- Harder to detect than a simple logout

**Special Considerations**:
- JSON API endpoint (not HTML form)
- Requires header-based CSRF protection (X-CSRF-Token)
- JavaScript client must obtain and send token
- Different pattern than form-based endpoints

---

## Identified Gaps

### Gap 1: Settings Page Logout Form

**Location**: `backend/app/templates/settings.html:16`

```html
<!-- Current (INSECURE) -->
<form method="POST" action="/logout" class="inline">
    <button type="submit"
            class="text-sm text-red-600 hover:text-red-800"
            data-testid="logout-button"
            aria-label="Logout">
        Logout
    </button>
</form>
```

**Missing**:
- No CSRF token hidden input field
- GET endpoint for `/settings` doesn't generate CSRF token
- POST `/logout` endpoint doesn't validate CSRF token

---

### Gap 2: Chat Page Logout Form

**Location**: `backend/app/templates/chat.html:30`

```html
<!-- Current (INSECURE) -->
<form method="POST" action="/logout" class="inline">
    <button type="submit"
            class="bg-gray-100 text-gray-700 hover:bg-gray-200 font-medium px-4 py-2 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition duration-150"
            data-testid="logout-button"
            aria-label="Logout from your account">
        Logout
    </button>
</form>
```

**Missing**:
- Same issues as settings page
- Affects more users (chat is primary interface)

---

### Gap 3: Chat Send JavaScript

**Location**: `backend/app/templates/chat.html:233`

```javascript
// Current (INSECURE)
const response = await fetch('/chat/send', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        message: userMessage,
        conversation_id: this.currentConversationId
    })
});
```

**Missing**:
- No X-CSRF-Token header
- No mechanism to obtain CSRF token from cookie
- Backend doesn't validate CSRF for this endpoint

---

## Proposed Solutions

### Visual Overview: CSRF Token Flow

The following diagrams show how CSRF tokens flow through the system using the Double Submit Cookie pattern.

**Form-Based Protection (Logout)**:
```
┌─────────────┐
│ GET /settings│
└──────┬──────┘
       │ 1. Generate csrf_token (unsigned) + signed_token
       ├──> Set cookie: fastapi-csrf-token=<signed_token>
       └──> Render form with: <input name="fastapi-csrf-token" value="<csrf_token>">

┌─────────────┐
│ POST /logout │
└──────┬──────┘
       │ 2. Read csrf_token from form field
       ├──> Read signed_token from cookie
       ├──> Validate: unsign(signed_token) == csrf_token
       └──> ✅ Success: Clear session
```

**Header-Based Protection (Chat)**:
```
┌─────────────┐
│ GET /chat/   │
└──────┬──────┘
       │ 1. Generate csrf_token + signed_token
       └──> Set cookie: fastapi-csrf-token=<signed_token>

┌─────────────┐
│POST /chat/send│
└──────┬──────┘
       │ 2. JavaScript reads cookie via document.cookie
       ├──> Send header: X-CSRF-Token: <signed_token>
       ├──> Validate: cookie value matches header value
       └──> ✅ Success: Process message
```

---

### Existing Pattern Reference: DELETE /garmin/link

Before implementing new protections, we reference the existing CSRF pattern already used in the codebase for consistency.

**Current Implementation**:
```python
# backend/app/routes/garmin.py (existing code)
@router.delete("/link")
async def unlink_garmin(
    request: Request,
    current_user: UserResponse = Depends(get_current_user),
    csrf_protect: CsrfProtect = Depends(),
) -> dict[str, str]:
    """Unlink Garmin account from user profile."""
    await csrf_protect.validate_csrf(request)
    # ... rest of implementation
```

**Frontend Pattern** (existing in templates):
```javascript
// Reads cookie and sends in X-CSRF-Token header
const csrfToken = document.cookie
    .split('; ')
    .find(row => row.startsWith('fastapi-csrf-token='))
    ?.split('=')[1];

// Send in DELETE request header
headers: {
    'X-CSRF-Token': csrfToken
}
```

**We will follow this exact pattern for `/chat/send` to maintain consistency.**

---

### Solution 1: Protect `/logout` Endpoint

#### Backend Changes

**File**: `backend/app/routes/auth.py`

```python
# Add CSRF validation to logout endpoint
@router.post("/logout")
async def logout(
    request: Request,
    csrf_protect: CsrfProtect = Depends(),
) -> Response:
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

#### Template Changes

**File**: `backend/app/templates/settings.html`

Update GET endpoint to generate CSRF token:

```python
# backend/app/routes/dashboard.py (or wherever settings route is)
@router.get("/settings", response_class=HTMLResponse)
async def settings_page(
    request: Request,
    current_user: UserResponse = Depends(get_current_user),
    csrf_protect: CsrfProtect = Depends(),
    templates: Jinja2Templates = Depends(get_templates),
) -> Response:
    """Display settings page with CSRF token."""
    csrf_token, signed_token = csrf_protect.generate_csrf_tokens()
    response = templates.TemplateResponse(
        request=request,
        name="settings.html",
        context={"csrf_token": csrf_token, "user": current_user},
    )
    csrf_protect.set_csrf_cookie(signed_token, response)
    return response
```

Update template to include CSRF token:

```html
<!-- backend/app/templates/settings.html -->
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

**File**: `backend/app/templates/chat.html`

Update GET endpoint to generate CSRF token:

```python
# backend/app/routes/chat.py
@router.get("/", response_class=HTMLResponse)
async def chat_page(
    request: Request,
    current_user: UserResponse = Depends(get_current_user),
    csrf_protect: CsrfProtect = Depends(),
    templates: Jinja2Templates = Depends(get_templates),
) -> Response:
    """Render chat interface page with CSRF token."""
    csrf_token, signed_token = csrf_protect.generate_csrf_tokens()
    response = templates.TemplateResponse(
        request=request,
        name="chat.html",
        context={"csrf_token": csrf_token, "user": current_user},
    )
    csrf_protect.set_csrf_cookie(signed_token, response)
    return response
```

Update template to include CSRF token:

```html
<!-- backend/app/templates/chat.html -->
<form method="POST" action="/logout" class="inline">
    <input type="hidden" name="fastapi-csrf-token" value="{{ csrf_token }}">
    <button type="submit"
            class="bg-gray-100 text-gray-700 hover:bg-gray-200 font-medium px-4 py-2 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition duration-150"
            data-testid="logout-button"
            aria-label="Logout from your account">
        Logout
    </button>
</form>
```

---

### Solution 2: Protect `/chat/send` Endpoint

This requires a different approach since it's a JSON API endpoint called from JavaScript.

#### Backend Changes

**File**: `backend/app/routes/chat.py`

```python
from fastapi_csrf_protect import CsrfProtect
from fastapi_csrf_protect.exceptions import CsrfProtectError

@router.post("/send")
async def send_message(
    request: Request,
    chat_request: ChatRequest,
    current_user: UserResponse = Depends(get_current_user),
    csrf_protect: CsrfProtect = Depends(),
) -> dict[str, Any]:
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
            detail="Security validation failed. Please refresh the page and try again."
        ) from e

    service = ChatService()
    try:
        response, conversation_id = await service.send_message(
            user_id=current_user.user_id, request=chat_request
        )
        return {"conversation_id": conversation_id, "response": response.model_dump()}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e
```

#### Frontend Changes

**File**: `backend/app/templates/chat.html`

Add JavaScript helper to read CSRF token from cookie:

```javascript
function chatInterface() {
    return {
        // ... existing properties ...

        // Helper: Get CSRF token from cookie
        getCsrfToken() {
            const name = 'fastapi-csrf-token';
            const value = `; ${document.cookie}`;
            const parts = value.split(`; ${name}=`);
            if (parts.length === 2) return parts.pop().split(';').shift();
            return null;
        },

        async sendMessage() {
            if (!this.messageInput.trim()) return;

            const userMessage = this.messageInput;
            this.messageInput = '';
            this.loading = true;
            this.error = null;

            try {
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
                        'X-CSRF-Token': csrfToken  // ← Add CSRF header
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
                // ... rest of existing code ...
            } catch (e) {
                console.error('Error sending message:', e);
                this.error = e.message || 'Failed to send message';
            } finally {
                this.loading = false;
            }
        },

        // ... rest of existing methods ...
    };
}
```

**Important Notes**:
- CSRF cookie must have `httponly=false` (already configured in `main.py:53`)
- JavaScript can read the cookie value and send it in `X-CSRF-Token` header
- `fastapi-csrf-protect` library checks headers before form fields (priority order)
- DELETE requests (like `/garmin/link`) already use this header pattern

#### Token Expiration Handling

**Scenario**: User opens chat page, leaves browser tab open for 2+ hours, returns and tries to send message.

**Current CSRF token TTL**: Configured in `fastapi-csrf-protect` settings (typically 1-2 hours)

**Solution**: Graceful degradation with automatic page reload

The JavaScript implementation above includes two levels of protection:

1. **Pre-flight check**: Detects missing token before making request
   ```javascript
   if (!csrfToken) {
       this.error = 'Security token expired. Please refresh the page.';
       return;
   }
   ```

2. **Post-response handling**: Catches 403 errors and auto-reloads
   ```javascript
   if (response.status === 403) {
       this.error = 'Your session has expired. Refreshing page...';
       setTimeout(() => window.location.reload(), 2000);
       return;
   }
   ```

**Alternative Approaches Considered**:
- ❌ **Background token refresh**: Complex, requires periodic API calls, increases server load
- ❌ **Long-lived tokens**: Reduces security, defeats purpose of token expiration
- ✅ **Graceful degradation with reload**: Simple, secure, good UX (user sees clear message)

**User Experience**:
- User sees friendly message: "Your session has expired. Refreshing page..."
- Page automatically reloads after 2 seconds
- New CSRF token is generated on page load
- User can immediately retry their action

---

## Implementation Plan

### Phase 1: Protect Logout Endpoint

**Estimated Time**: 1 hour

**Steps**:
1. **Audit all logout forms in codebase**
   - Search for all instances: `grep -r 'action="/logout"' backend/app/templates/`
   - Search for variations: `grep -r 'action=\"/logout\"' backend/app/templates/`
   - Search broadly: `grep -r '/logout' backend/app/templates/ | grep -i form`
   - Document all found instances (expected: settings.html, chat.html)
   - Verify no additional logout forms exist

2. **Verify CSRF cookie configuration**
   - Open `backend/app/main.py`
   - Verify configuration:
     ```python
     csrf_settings.cookie_httponly = False  # Required for JavaScript access
     csrf_settings.cookie_samesite = "lax"  # CSRF protection
     csrf_settings.cookie_secure = True     # HTTPS only (production)
     ```
   - If missing or incorrect, update configuration

3. Update `/logout` endpoint in `backend/app/routes/auth.py`
   - Add `csrf_protect` dependency
   - Add `await csrf_protect.validate_csrf(request)` call

4. Find and update GET endpoint for `/settings` page
   - Add `csrf_protect` dependency
   - Generate CSRF token pair
   - Pass `csrf_token` to template context
   - Set CSRF cookie on response

5. Update `backend/app/templates/settings.html`
   - Add hidden input with `name="fastapi-csrf-token"` and `value="{{ csrf_token }}"`

6. Update GET endpoint for `/chat` page (same pattern as settings)

7. Update `backend/app/templates/chat.html` logout form
   - Add hidden input with CSRF token

8. Write integration tests
   - Test logout without CSRF token (should fail with 403)
   - Test logout with valid CSRF token (should succeed)
   - Test failed logout preserves session (user still logged in after 403)
   - Test logout with expired token (should fail with 403)

**Success Criteria**:
- [ ] All logout forms in codebase identified (audit complete)
- [ ] CSRF cookie has `httponly=false` (verified in code)
- [ ] CSRF cookie has `samesite=lax` (verified in code)
- [ ] `/logout` endpoint validates CSRF token
- [ ] Settings page logout form includes CSRF token
- [ ] Chat page logout form includes CSRF token
- [ ] Integration tests pass
- [ ] Manual testing: logout still works normally
- [ ] Manual testing: forged logout request is blocked

---

### Phase 2: Protect Chat Send Endpoint

**Estimated Time**: 1.5 hours

**Steps**:
1. Update `/chat/send` endpoint in `backend/app/routes/chat.py`
   - Add `csrf_protect` dependency
   - Add `await csrf_protect.validate_csrf(request)` call
2. Update `backend/app/templates/chat.html` JavaScript
   - Add `getCsrfToken()` helper function
   - Update `sendMessage()` to include `X-CSRF-Token` header
3. Write integration tests
   - Test chat send without CSRF token (should fail with 403)
   - Test chat send with valid CSRF token in header (should succeed)
   - Test chat send with invalid token (should fail)
4. Write E2E tests (optional but recommended)
   - Test chat interface sends CSRF token automatically
   - Test chat submission works end-to-end

**Success Criteria**:
- [ ] `/chat/send` endpoint validates CSRF token
- [ ] Chat interface JavaScript sends X-CSRF-Token header
- [ ] Integration tests pass
- [ ] Manual testing: chat messages still send normally
- [ ] Manual testing: forged chat request (without token) is blocked

---

### Phase 3: Documentation and Testing

**Estimated Time**: 0.5 hours

**Steps**:
1. Update `docs/development/csrf/CSRF_SPECIFICATION.md`
   - Add `/logout` and `/chat/send` to protected endpoints table
   - Document header-based CSRF for JSON APIs
2. Update manual testing runsheet (if exists)
   - Add logout CSRF test
   - Add chat send CSRF test
3. Run full test suite
   - Verify all existing tests still pass
   - Verify 80%+ coverage maintained
4. Run security scan
   - `bandit` should pass with no new issues

**Success Criteria**:
- [ ] Documentation updated
- [ ] All tests passing (unit, integration, E2E)
- [ ] 80%+ test coverage maintained
- [ ] Security scan passes

---

## Testing Strategy

### Unit Tests

**New File**: `backend/tests/unit/test_logout_csrf.py`

```python
"""Unit tests for logout CSRF protection."""

import pytest
from unittest.mock import Mock
from fastapi_csrf_protect import CsrfProtect
from fastapi_csrf_protect.exceptions import CsrfProtectError

def test_logout_validates_csrf_token():
    """Test that logout endpoint requires CSRF validation."""
    # This is more of an integration test
    # Unit test would mock CsrfProtect.validate_csrf
    pass
```

### Integration Tests

**File**: `backend/tests/integration/test_csrf_routes.py` (add to existing file)

```python
def test_logout_requires_csrf_token(client: TestClient):
    """Test that /logout rejects requests without CSRF token."""
    # Login first
    login_response = client.get("/login")
    csrf_cookie = login_response.cookies.get("fastapi-csrf-token")

    soup = BeautifulSoup(login_response.text, "html.parser")
    csrf_input = soup.find("input", {"name": "fastapi-csrf-token"})
    csrf_token = csrf_input["value"]

    client.post(
        "/auth/login",
        data={
            "username": "test@example.com",
            "password": "TestPass123",
            "fastapi-csrf-token": csrf_token,
        },
        cookies={"fastapi-csrf-token": csrf_cookie},
    )

    # Attempt logout without CSRF token
    response = client.post("/logout")

    assert response.status_code == 403
    assert "CSRF" in response.text or "Security validation" in response.text


def test_logout_with_valid_csrf_token(client: TestClient):
    """Test that /logout succeeds with valid CSRF token."""
    # Login and get CSRF token
    # ... (similar setup as above)

    # Get settings page to obtain CSRF token
    settings_response = client.get("/settings")
    csrf_cookie = settings_response.cookies.get("fastapi-csrf-token")

    soup = BeautifulSoup(settings_response.text, "html.parser")
    csrf_input = soup.find("input", {"name": "fastapi-csrf-token"})
    csrf_token = csrf_input["value"]

    # Logout with valid token
    response = client.post(
        "/logout",
        data={"fastapi-csrf-token": csrf_token},
        cookies={"fastapi-csrf-token": csrf_cookie},
    )

    assert response.status_code == 303  # Redirect
    assert response.headers["Location"] == "/login"


def test_chat_send_requires_csrf_token(authenticated_client: TestClient):
    """Test that /chat/send rejects requests without CSRF token."""
    response = authenticated_client.post(
        "/chat/send",
        json={
            "message": "Test message",
            "conversation_id": None,
        },
        # No X-CSRF-Token header
    )

    assert response.status_code == 403


def test_chat_send_with_valid_csrf_token(authenticated_client: TestClient):
    """Test that /chat/send succeeds with valid CSRF token in header."""
    # Get chat page to obtain CSRF token
    chat_response = authenticated_client.get("/chat/")
    csrf_cookie = chat_response.cookies.get("fastapi-csrf-token")

    # Extract token from cookie (in real JavaScript, read from document.cookie)
    csrf_token = csrf_cookie

    response = authenticated_client.post(
        "/chat/send",
        json={
            "message": "Test message",
            "conversation_id": None,
        },
        headers={"X-CSRF-Token": csrf_token},
        cookies={"fastapi-csrf-token": csrf_cookie},
    )

    assert response.status_code == 200
    data = response.json()
    assert "conversation_id" in data
    assert "response" in data


def test_logout_failed_attempt_preserves_session(client: TestClient):
    """Test that failed CSRF logout doesn't clear session."""
    # Login first
    login_response = client.get("/login")
    csrf_cookie = login_response.cookies.get("fastapi-csrf-token")

    soup = BeautifulSoup(login_response.text, "html.parser")
    csrf_input = soup.find("input", {"name": "fastapi-csrf-token"})
    csrf_token = csrf_input["value"]

    login_result = client.post(
        "/auth/login",
        data={
            "username": "test@example.com",
            "password": "TestPass123",
            "fastapi-csrf-token": csrf_token,
        },
        cookies={"fastapi-csrf-token": csrf_cookie},
    )

    # Attempt logout WITHOUT CSRF token (should fail)
    logout_response = client.post("/logout")
    assert logout_response.status_code == 403

    # Verify user is STILL logged in
    protected_response = client.get("/chat/")
    assert protected_response.status_code == 200
    assert "logout-button" in protected_response.text  # Still authenticated


def test_chat_send_with_expired_token(authenticated_client: TestClient):
    """Test that expired CSRF token is rejected."""
    from freezegun import freeze_time

    # Generate token at time T
    with freeze_time("2024-01-01 10:00:00"):
        chat_response = authenticated_client.get("/chat/")
        csrf_token = chat_response.cookies.get("fastapi-csrf-token")

    # Fast forward time by 3 hours (assuming 2-hour token TTL)
    with freeze_time("2024-01-01 13:00:00"):
        response = authenticated_client.post(
            "/chat/send",
            json={"message": "Test", "conversation_id": None},
            headers={"X-CSRF-Token": csrf_token},
            cookies={"fastapi-csrf-token": csrf_token},
        )

    assert response.status_code == 403
    assert "expired" in response.json()["detail"].lower() or "security" in response.json()["detail"].lower()


def test_logout_with_invalid_token(client: TestClient):
    """Test that logout with tampered CSRF token is rejected."""
    # Login first
    login_response = client.get("/login")
    csrf_cookie = login_response.cookies.get("fastapi-csrf-token")

    soup = BeautifulSoup(login_response.text, "html.parser")
    csrf_input = soup.find("input", {"name": "fastapi-csrf-token"})
    csrf_token = csrf_input["value"]

    client.post(
        "/auth/login",
        data={
            "username": "test@example.com",
            "password": "TestPass123",
            "fastapi-csrf-token": csrf_token,
        },
        cookies={"fastapi-csrf-token": csrf_cookie},
    )

    # Get settings page to obtain CSRF token
    settings_response = client.get("/settings")
    csrf_cookie = settings_response.cookies.get("fastapi-csrf-token")

    # Tamper with token (flip some characters)
    tampered_token = "tampered_invalid_token_12345"

    # Attempt logout with invalid token
    response = client.post(
        "/logout",
        data={"fastapi-csrf-token": tampered_token},
        cookies={"fastapi-csrf-token": csrf_cookie},
    )

    assert response.status_code == 403
```

### E2E Tests

**File**: `backend/tests/e2e_playwright/test_csrf_protection.py` (add to existing file)

```python
def test_logout_csrf_protection_blocks_attack(page: Page, base_url: str):
    """Test that logout CSRF protection blocks cross-origin attacks."""
    # 1. User logs into Selflytics
    page.goto(f"{base_url}/login")
    page.fill('input[name="username"]', "test@example.com")
    page.fill('input[name="password"]', "TestPass123")
    page.click('button[type="submit"]')
    expect(page).to_have_url(f"{base_url}/chat/")

    # 2. Simulate attacker's malicious page
    malicious_html = f"""
    <html>
    <body onload="document.forms[0].submit()">
        <form action="{base_url}/logout" method="POST">
            <!-- No CSRF token -->
        </form>
    </body>
    </html>
    """

    # Navigate to malicious page
    page.set_content(malicious_html)
    page.wait_for_load_state("networkidle")

    # 3. Verify user is still logged in (attack blocked)
    page.goto(f"{base_url}/chat/")
    expect(page.locator('[data-testid="logout-button"]')).to_be_visible()
    # User still logged in - attack was blocked


def test_legitimate_logout_works(page: Page, base_url: str):
    """Test that legitimate logout (with CSRF token) still works."""
    # Login
    page.goto(f"{base_url}/login")
    page.fill('input[name="username"]', "test@example.com")
    page.fill('input[name="password"]', "TestPass123")
    page.click('button[type="submit"]')

    # Go to settings page
    page.goto(f"{base_url}/settings")

    # Click logout button (includes CSRF token)
    page.click('[data-testid="logout-button"]')

    # Verify redirected to login page
    expect(page).to_have_url(f"{base_url}/login")


def test_chat_send_includes_csrf_token(page: Page, authenticated_page: Page, base_url: str):
    """Test that chat interface includes CSRF token in requests."""
    authenticated_page.goto(f"{base_url}/chat/")

    # Intercept /chat/send request to verify headers
    requests = []

    def handle_request(request):
        if "/chat/send" in request.url:
            requests.append(request)

    authenticated_page.on("request", handle_request)

    # Send a message
    authenticated_page.fill('input[type="text"]', "Test message")
    authenticated_page.click('button[type="submit"]')

    # Wait for request
    authenticated_page.wait_for_timeout(1000)

    # Verify request included X-CSRF-Token header
    assert len(requests) > 0
    chat_request = requests[0]
    assert "X-CSRF-Token" in chat_request.headers
    assert chat_request.headers["X-CSRF-Token"] != ""
```

---

## Testing Coverage Matrix

The following matrix ensures comprehensive test coverage across all scenarios:

| Scenario | Unit | Integration | E2E | Priority | Notes |
|----------|------|-------------|-----|----------|-------|
| Logout without token | - | ✅ | ✅ | High | Core security check |
| Logout with valid token | - | ✅ | ✅ | High | Verify normal flow works |
| Logout with invalid token | - | ✅ | - | Medium | Tampered token detection |
| Logout with expired token | - | ✅ | - | Medium | Time-based validation |
| Failed logout preserves session | - | ✅ | - | High | No unintended logout |
| Chat send without token | - | ✅ | - | High | Core security check |
| Chat send with valid token | - | ✅ | ✅ | High | Verify normal flow works |
| Chat send with invalid token | - | ✅ | - | Medium | Header validation |
| Chat send with expired token | - | ✅ | - | Medium | Time-based validation |
| JavaScript handles missing token | - | - | ✅ | High | Client-side error handling |
| JavaScript handles 403 gracefully | - | - | ✅ | High | Auto-refresh on expiration |
| Cross-origin logout attack blocked | - | - | ✅ | Medium | Real CSRF attack scenario |
| All logout forms have tokens | - | - | ✅ | High | Visual verification |

**Coverage Goals**:
- ✅ **Integration tests**: Cover all backend validation logic (80%+ coverage)
- ✅ **E2E tests**: Cover critical user journeys and attack scenarios
- ✅ **Manual testing**: Verify user experience and error messages

**Test Dependencies**:
- Integration tests may require `freezegun` for time-based token expiration tests
- E2E tests require Playwright and local Firestore emulator
- Cross-origin tests may need to serve malicious HTML (use Playwright's `page.set_content()`)

---

## References

### Internal Documentation

- **Parent Specification**: `docs/development/csrf/CSRF_SPECIFICATION.md` - Original CSRF implementation
- **CSRF Roadmap**: `docs/development/csrf/ROADMAP.md` - PR #21 implementation details
- **Development Workflow**: `docs/DEVELOPMENT_WORKFLOW.md` - TDD practices

### Standards & Best Practices

- **OWASP CSRF Prevention**: https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html
- **OWASP Top 10 (2021)**: A01:2021 – Broken Access Control (includes CSRF)

### Libraries & Tools

- **fastapi-csrf-protect**: https://github.com/aekasitt/fastapi-csrf-protect
  - Supports both form-based (POST) and header-based (JSON API) CSRF protection
  - Flexible mode checks headers first, then form fields

### Related Issues & PRs

- **Issue #12**: Integrate CSRF protection into settings page logout form
- **PR #21**: Initial CSRF protection implementation (merged)
- **Issue #8**: Original CSRF protection requirement

---

## Appendix: Risk Matrix

| Endpoint | Risk Level | Impact if Exploited | Likelihood | Priority |
|----------|-----------|---------------------|------------|----------|
| `/logout` | Medium | User forced to re-login | Medium | High (easy fix) |
| `/chat/send` | Medium-High | Unwanted messages, resource consumption, potential info leak | Medium | High (more complex) |

**Priority Justification**:
- Both gaps should be fixed for comprehensive security
- `/logout` is simpler (form-based, follows existing patterns)
- `/chat/send` is more complex (JSON API, requires header approach)
- Both are straightforward given existing CSRF infrastructure

---

## Appendix: Optional Enhancement - Rate Limiting

While CSRF protection prevents unauthorized cross-site requests, **rate limiting** provides defense-in-depth against abuse and DoS attacks. This is **outside the scope** of CSRF protection but recommended for production systems.

### Recommended Implementation

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post("/logout")
@limiter.limit("10/minute")  # Prevent logout spam
async def logout(
    request: Request,
    csrf_protect: CsrfProtect = Depends(),
) -> Response:
    """Logout user by clearing authentication cookie."""
    await csrf_protect.validate_csrf(request)
    # ... rest of implementation


@router.post("/send")
@limiter.limit("30/minute")  # Prevent chat spam and API cost abuse
async def send_message(
    request: Request,
    chat_request: ChatRequest,
    current_user: UserResponse = Depends(get_current_user),
    csrf_protect: CsrfProtect = Depends(),
) -> dict[str, Any]:
    """Send chat message and get AI response."""
    try:
        await csrf_protect.validate_csrf(request)
    except CsrfProtectError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Security validation failed. Please refresh the page and try again."
        ) from e
    # ... rest of implementation
```

### Benefits

- **DoS Protection**: Prevents attacker from overwhelming server with requests
- **Cost Control**: Limits OpenAI API calls even if attacker bypasses CSRF
- **Resource Protection**: Prevents Firestore quota exhaustion
- **User Protection**: Prevents accidental client-side loops from causing issues

### Configuration Considerations

- **Logout limit** (10/minute): Legitimate users rarely logout more than once per minute
- **Chat limit** (30/minute): Allows normal conversation flow but blocks spam
- **Key function**: `get_remote_address` rate-limits by IP (consider user ID for authenticated endpoints)

### Implementation Timing

- ✅ **Recommended**: Implement after CSRF protection is complete
- ✅ **Priority**: Medium (nice-to-have, not security-critical)
- ✅ **Effort**: Low (30 minutes, add dependency + decorators)

---

## Appendix: Troubleshooting

### Common Issues and Solutions

#### Issue 1: "403 Forbidden" on Logout

**Symptom**: Clicking logout button shows error instead of logging out.

**Possible Causes**:
1. CSRF token missing from form
2. Cookie not set by GET endpoint
3. Token mismatch between cookie and form
4. Token expired

**Diagnostic Steps**:
```bash
# 1. Check template includes hidden input
grep -A5 'action="/logout"' backend/app/templates/settings.html
# Expected: <input type="hidden" name="fastapi-csrf-token" value="{{ csrf_token }}">

# 2. Check GET endpoint generates token
grep -A10 'def settings_page' backend/app/routes/dashboard.py
# Expected: csrf_protect.generate_csrf_tokens() and set_csrf_cookie()

# 3. Check browser cookies (in browser DevTools)
# Application tab → Cookies → Should see "fastapi-csrf-token"

# 4. Check form submission (in browser Network tab)
# POST /logout → Payload → Should contain "fastapi-csrf-token" field
```

**Solution**:
- If template missing token → Add `<input type="hidden" name="fastapi-csrf-token" value="{{ csrf_token }}">`
- If cookie not set → Update GET endpoint to call `set_csrf_cookie()`
- If token mismatch → Verify both cookie and form use same token source
- If token expired → User needs to refresh page (or implement auto-refresh)

---

#### Issue 2: "Failed to send message" in Chat

**Symptom**: Chat messages fail to send with security error.

**Possible Causes**:
1. JavaScript cannot read CSRF cookie
2. CSRF token expired
3. `X-CSRF-Token` header not sent
4. `getCsrfToken()` returns `null`

**Diagnostic Steps**:
```bash
# 1. Check cookie is readable by JavaScript
grep "cookie_httponly" backend/app/main.py
# Expected: csrf_settings.cookie_httponly = False

# 2. Open browser console → Network tab → Click failed request
# Headers tab → Request Headers → Should see "X-CSRF-Token: <value>"
# Cookies tab → Should see "fastapi-csrf-token"

# 3. Test getCsrfToken() function
# Browser console:
# > document.cookie.split('; ').find(row => row.startsWith('fastapi-csrf-token='))
# Expected: "fastapi-csrf-token=<some-value>"
```

**Solution**:
- If cookie httponly=true → Change to `cookie_httponly=False` in `main.py`
- If X-CSRF-Token header missing → Check JavaScript includes header in fetch call
- If getCsrfToken() returns null → User needs to refresh page to get new token
- If token expired → JavaScript should show "Session expired, refreshing..." and reload

---

#### Issue 3: Chat Page Stuck in "Refreshing..." Loop

**Symptom**: Page keeps reloading after "Your session has expired" message.

**Possible Causes**:
1. CSRF cookie not being set on page reload
2. Infinite 403 loop (missing token on reload)

**Diagnostic Steps**:
```bash
# 1. Check GET /chat/ endpoint sets CSRF cookie
grep -A15 "def chat_page" backend/app/routes/chat.py
# Expected: csrf_protect.set_csrf_cookie(signed_token, response)

# 2. Check browser Network tab during reload
# GET /chat/ → Response Headers → Should see "Set-Cookie: fastapi-csrf-token=..."
```

**Solution**:
- Ensure GET `/chat/` endpoint calls `set_csrf_cookie()` to regenerate token on page load
- Clear browser cookies and cache, then retry
- Check server logs for errors during token generation

---

#### Issue 4: Integration Tests Fail with "CSRF token not found"

**Symptom**: Tests fail even though code looks correct.

**Possible Causes**:
1. Test client not preserving cookies between requests
2. Test not extracting token correctly from response
3. Test not sending both cookie AND form field/header

**Solution**:
```python
# CORRECT test pattern:
def test_logout_with_csrf(client: TestClient):
    # 1. GET page to obtain token
    response = client.get("/settings")

    # 2. Extract cookie
    csrf_cookie = response.cookies.get("fastapi-csrf-token")

    # 3. Extract token from HTML (for forms)
    soup = BeautifulSoup(response.text, "html.parser")
    csrf_input = soup.find("input", {"name": "fastapi-csrf-token"})
    csrf_token = csrf_input["value"]

    # 4. Send BOTH in POST request
    result = client.post(
        "/logout",
        data={"fastapi-csrf-token": csrf_token},  # Form field
        cookies={"fastapi-csrf-token": csrf_cookie},  # Cookie
    )

    assert result.status_code == 303  # Success
```

---

#### Issue 5: E2E Tests Timeout on Chat Send

**Symptom**: Playwright tests hang when submitting chat messages.

**Possible Causes**:
1. Chat form waiting for AI response indefinitely
2. JavaScript error preventing form submission
3. CSRF token issue blocking request

**Diagnostic Steps**:
```bash
# Run E2E tests in headed mode to see browser
uv --directory backend run pytest tests/e2e_playwright -v --headed

# Check browser console for JavaScript errors
# Check Network tab for failed requests
```

**Solution**:
- Mock AI service in tests to avoid waiting for real OpenAI responses
- Check browser console for JavaScript errors
- Add timeout to Playwright assertions: `expect(element).to_be_visible(timeout=10000)`
- Verify CSRF token is available before test runs (check cookie in DevTools)

---

### Quick Reference Commands

```bash
# Search for all logout forms
grep -rn 'action="/logout"' backend/app/templates/

# Check CSRF configuration
grep -A5 "csrf_settings" backend/app/main.py

# Run only CSRF integration tests
uv --directory backend run pytest tests/integration/test_csrf_routes.py -v

# Run only CSRF E2E tests
uv --directory backend run pytest tests/e2e_playwright/test_csrf_protection.py -v --headed

# Check test coverage for CSRF code
uv --directory backend run pytest tests/ -v --cov=app.routes.auth --cov=app.routes.chat

# Search for CSRF validate calls
grep -rn "validate_csrf" backend/app/routes/
```

---

**End of Specification**
