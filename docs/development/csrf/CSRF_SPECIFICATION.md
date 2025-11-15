# CSRF Protection Specification for Selflytics

## Document Information

- **Version**: 1.0
- **Last Updated**: 2025-11-14
- **Status**: Draft
- **Related Issue**: [#8 - Add CSRF protection to all POST forms](https://github.com/anbaricidias/selflytics/issues/8)

## Table of Contents

1. [Overview](#overview)
2. [Security Context](#security-context)
3. [CSRF Attack Scenarios](#csrf-attack-scenarios)
4. [Protection Strategy](#protection-strategy)
5. [Technical Implementation](#technical-implementation)
6. [HTMX Integration](#htmx-integration)
7. [User Journeys](#user-journeys)
8. [Testing Requirements](#testing-requirements)
9. [References](#references)

---

## Overview

### What is CSRF?

Cross-Site Request Forgery (CSRF) is an attack that forces an authenticated user to execute unwanted actions on a web application. The attack works because:

1. **Authentication persists** - Browsers automatically send cookies with every request
2. **No origin verification** - Without CSRF protection, the server cannot distinguish legitimate requests from forged ones
3. **State-changing operations** - POST/PUT/DELETE endpoints can be exploited

### Why Selflytics Needs CSRF Protection

Selflytics uses **cookie-based authentication** for browser sessions:

```python
# backend/app/routes/auth.py:134
response.set_cookie(
    key="access_token",
    value=f"Bearer {access_token}",
    httponly=True,
    secure=settings.environment != "development",
    samesite="lax",  # ⚠️ Vulnerable to CSRF attacks
    max_age=1800,
)
```

**Vulnerability**: While `samesite="lax"` provides some protection, it **does not protect against**:
- Same-site attacks (attacker controls a subdomain)
- User-initiated navigation (GET requests that trigger form submissions)
- Browser bugs or future relaxations of SameSite enforcement

**Current Attack Surface**:
- `/auth/register` - Could create unwanted accounts
- `/auth/login` - Could force login to attacker's account
- `/garmin/link` - **HIGH RISK** - Could link attacker's Garmin account to victim's Selflytics account
- `/garmin/sync` - Could trigger unwanted data syncs

---

## Security Context

### Current Authentication Architecture

```
┌─────────────┐          ┌──────────────┐          ┌─────────────┐
│   Browser   │          │   FastAPI    │          │  Firestore  │
│             │          │   Backend    │          │             │
└──────┬──────┘          └──────┬───────┘          └──────┬──────┘
       │                        │                         │
       │  POST /auth/login      │                         │
       ├───────────────────────>│                         │
       │  (email + password)    │  Verify credentials     │
       │                        ├────────────────────────>│
       │                        │<────────────────────────┤
       │  200 OK + Set-Cookie   │                         │
       │  access_token=JWT...   │                         │
       │<───────────────────────┤                         │
       │                        │                         │
       │  GET /dashboard        │                         │
       │  Cookie: access_token  │                         │
       ├───────────────────────>│                         │
       │                        │  Verify JWT             │
       │                        │  (from cookie)          │
       │                        ├─────────┐               │
       │  200 OK (HTML)         │         │               │
       │<───────────────────────┤<────────┘               │
```

**Key Points**:
1. JWT stored in `httponly` cookie (XSS-resistant)
2. Cookie sent automatically by browser (CSRF-vulnerable)
3. No request origin verification
4. HTMX partial updates complicate token refresh

---

## CSRF Attack Scenarios

### Scenario 1: Garmin Account Linking Attack (HIGH SEVERITY)

**Attack Goal**: Link attacker's Garmin account to victim's Selflytics account

**Prerequisites**:
- Victim is logged into Selflytics (has valid `access_token` cookie)
- Victim visits attacker's malicious website

**Attack Flow**:

```html
<!-- Attacker's malicious site: evil.com -->
<!DOCTYPE html>
<html>
<body onload="document.forms[0].submit()">
  <form action="https://selflytics.app/garmin/link" method="POST">
    <input type="hidden" name="username" value="attacker@evil.com">
    <input type="hidden" name="password" value="attackers-garmin-password">
  </form>
</body>
</html>
```

**Step-by-Step Attack**:

1. **Victim authenticates** to Selflytics
   ```
   Browser Cookie: access_token=Bearer eyJ0eXAi...
   ```

2. **Victim visits** `evil.com` (via phishing email, forum link, etc.)

3. **Attacker's page auto-submits** form to Selflytics
   ```http
   POST /garmin/link HTTP/1.1
   Host: selflytics.app
   Cookie: access_token=Bearer eyJ0eXAi...  ← Browser sends automatically!
   Content-Type: application/x-www-form-urlencoded

   username=attacker@evil.com&password=attackers-garmin-password
   ```

4. **Selflytics backend processes** the request:
   ```python
   # backend/app/routes/garmin.py:34-42
   @router.post("/garmin/link")
   async def link_garmin_account(
       username: str = Form(...),
       password: str = Form(...),
       current_user: UserResponse = Depends(get_current_user),  # ✅ Valid!
   ):
       # ⚠️ NO CSRF CHECK - request is accepted!
       service = GarminService(current_user.user_id)
       success = await service.link_account(username, password)
   ```

5. **Result**: Attacker's Garmin account is now linked to victim's Selflytics profile
   - Attacker can now see victim's AI analysis of *their* (attacker's) fitness data
   - Victim sees attacker's data instead of their own
   - Victim's actual Garmin data is not synced

**Impact**:
- ⚠️ **Account confusion** - Victim sees wrong data
- ⚠️ **Privacy violation** - Attacker can manipulate what victim sees
- ⚠️ **Service disruption** - Victim cannot use legitimate Garmin integration
- ⚠️ **Potential data exfiltration** - If attacker can later unlink and victim re-links, attacker might gain access to victim's sync history

---

### Scenario 2: Forced Account Registration

**Attack Goal**: Create unwanted user accounts to spam the service or consume resources

**Attack Flow**:

```html
<!-- evil.com -->
<iframe name="hidden-iframe" style="display:none"></iframe>
<form id="spam-form" action="https://selflytics.app/auth/register"
      method="POST" target="hidden-iframe">
  <input type="hidden" name="email" value="spam-001@tempmail.com">
  <input type="hidden" name="password" value="RandomPass123">
  <input type="hidden" name="display_name" value="Spam User 001">
</form>
<script>
  // Submit multiple forms in rapid succession
  for (let i = 0; i < 100; i++) {
    let form = document.getElementById('spam-form').cloneNode(true);
    form.elements['email'].value = `spam-${i}@tempmail.com`;
    document.body.appendChild(form);
    form.submit();
  }
</script>
```

**Impact**:
- Database bloat
- Resource consumption
- Analytics pollution
- Potential DoS

---

### Scenario 3: Session Fixation via Forced Login

**Attack Goal**: Force victim to log into attacker's account

**Attack Flow**:

1. Attacker creates Selflytics account with malicious content
2. Attacker crafts form that logs victim into attacker's account:
   ```html
   <form action="https://selflytics.app/auth/login" method="POST">
     <input type="hidden" name="username" value="attacker@evil.com">
     <input type="hidden" name="password" value="attackers-password">
   </form>
   ```
3. Victim submits form unknowingly
4. Victim now sees attacker's dashboard with malicious content/links
5. If victim enters sensitive info (credit card for premium features), attacker can access it

**Impact**:
- ⚠️ Phishing attacks
- ⚠️ Credential theft
- ⚠️ Malware distribution

---

## Protection Strategy

### Selected Library: fastapi-csrf-protect

**Why this library?**
- ✅ Designed specifically for FastAPI
- ✅ Supports both API (header-based) and form (token-based) protection
- ✅ Simple integration with Jinja2 templates
- ✅ Configurable token expiration
- ✅ Active maintenance

**Repository**: https://github.com/aekasitt/fastapi-csrf-protect

### Protection Mechanism: Double Submit Cookie Pattern

```
┌─────────────┐          ┌──────────────┐
│   Browser   │          │   FastAPI    │
└──────┬──────┘          └──────┬───────┘
       │                        │
       │  GET /login            │
       ├───────────────────────>│
       │                        │  Generate CSRF token
       │                        │  csrf_token = secrets.token_urlsafe(32)
       │                        ├─────────┐
       │  200 OK                │         │
       │  Set-Cookie: csrf...   │<────────┘
       │  HTML with token       │
       │<───────────────────────┤
       │                        │
       │  POST /auth/login      │
       │  Cookie: csrf...       │
       │  Body: csrf_token=...  │
       ├───────────────────────>│
       │                        │  Verify:
       │                        │  cookie == body token?
       │                        ├─────────┐
       │                        │         │
       │  200 OK / 403 Forbidden│<────────┘
       │<───────────────────────┤
```

**How it works**:
1. **Server generates** random CSRF token when rendering form
2. **Server sends token** in both cookie AND hidden form field
3. **Browser submits** both cookie and form field
4. **Server validates** that both values match
5. **Attacker cannot forge** because they cannot:
   - Read victim's cookies (same-origin policy)
   - Set cookies for selflytics.app domain from evil.com

---

## Technical Implementation

### 1. Configuration (backend/app/main.py)

```python
from fastapi_csrf_protect import CsrfProtect
from fastapi_csrf_protect.exceptions import CsrfProtectError
from pydantic import BaseModel

# CSRF Settings
class CsrfSettings(BaseModel):
    secret_key: str  # Load from environment variable
    cookie_name: str = "csrf_token"
    cookie_samesite: str = "strict"  # Stricter than auth cookie
    cookie_secure: bool = True  # HTTPS only in production
    cookie_httponly: bool = False  # Must be readable by JavaScript (for HTMX)
    cookie_domain: str | None = None
    header_name: str = "X-CSRF-Token"
    max_age: int = 3600  # 1 hour

# Load CSRF configuration
@CsrfProtect.load_config
def get_csrf_config():
    settings = get_settings()
    return CsrfSettings(
        secret_key=settings.csrf_secret,  # New env var
        cookie_secure=settings.environment != "development",
    )

# Exception handler
@app.exception_handler(CsrfProtectError)
async def csrf_protect_exception_handler(request: Request, exc: CsrfProtectError):
    """Handle CSRF validation failures."""
    accept_header = request.headers.get("accept", "")
    hx_request = request.headers.get("HX-Request", "") == "true"
    is_browser = "text/html" in accept_header or hx_request

    if is_browser:
        # For HTMX requests, return error fragment
        if hx_request:
            return templates.TemplateResponse(
                request=request,
                name="fragments/csrf_error.html",
                status_code=403,
            )
        # For full page requests, show error page
        return templates.TemplateResponse(
            request=request,
            name="error/403.html",
            context={"detail": "CSRF validation failed. Please refresh and try again."},
            status_code=403,
        )

    # For API requests, return JSON
    return JSONResponse(
        status_code=403,
        content={"detail": "CSRF validation failed"},
    )
```

### 2. Environment Configuration

Add to `backend/.env.example`:

```bash
# CSRF Protection
CSRF_SECRET="change-this-in-production-min-32-chars"
```

Add to `backend/app/config.py`:

```python
class Settings(BaseSettings):
    # ... existing fields ...

    # CSRF Protection
    csrf_secret: str = Field(
        default="dev-csrf-secret-change-in-production",
        description="CSRF token secret key (min 32 characters)",
    )
```

### 3. Route Protection

#### Example: /auth/register

```python
from fastapi_csrf_protect import CsrfProtect

@router.post("/auth/register")
async def register(
    request: Request,
    csrf_protect: CsrfProtect = Depends(),  # ← Add CSRF dependency
    email: str = Form(...),
    password: str = Form(...),
    display_name: str = Form(...),
    confirm_password: str = Form(None),
    user_service: UserService = Depends(get_user_service),
    templates=Depends(get_templates),
):
    """Register a new user."""

    # Validate CSRF token
    await csrf_protect.validate_csrf(request)  # ← Validate before processing

    # ... rest of endpoint logic ...
```

#### Pattern for All Protected Routes

```python
# CSRF-protected POST endpoint pattern
@router.post("/endpoint")
async def endpoint(
    request: Request,
    csrf_protect: CsrfProtect = Depends(),  # 1. Add dependency
    # ... other dependencies ...
):
    await csrf_protect.validate_csrf(request)  # 2. Validate FIRST
    # ... business logic ...
```

### 4. Template Integration

#### Generating Tokens in Templates

Modify GET endpoints to pass CSRF token:

```python
from fastapi_csrf_protect import CsrfProtect

@router.get("/register", response_class=HTMLResponse)
async def register_form(
    request: Request,
    csrf_protect: CsrfProtect = Depends(),
    templates=Depends(get_templates),
):
    """Display registration form with CSRF token."""
    csrf_token, signed_token = csrf_protect.generate_csrf_tokens()
    response = templates.TemplateResponse(
        request=request,
        name="register.html",
        context={"csrf_token": csrf_token},  # ← Pass to template
    )
    csrf_protect.set_csrf_cookie(signed_token, response)  # ← Set cookie
    return response
```

#### Adding Tokens to Forms

**Example: backend/app/templates/fragments/register_form.html**

```html
<form
    hx-post="/auth/register"
    hx-swap="outerHTML"
    x-data="{ loading: false }"
    @submit="loading = true"
    data-reset-loading-on-swap
    class="space-y-5"
>
    <!-- CSRF Token (MUST be first field) -->
    <input type="hidden" name="csrf_token" value="{{ csrf_token }}">

    <!-- ... rest of form fields ... -->
</form>
```

**Key Points**:
- ✅ Hidden input field named `csrf_token`
- ✅ Value from template context
- ✅ Should be first field in form (best practice)
- ✅ Works with HTMX partial updates

---

## HTMX Integration

### Challenge: Partial DOM Updates

HTMX swaps HTML fragments without full page reloads. This creates challenges:

1. **Token Refresh**: How to get new CSRF token after form submission?
2. **Cookie Sync**: How to ensure cookie is set when fragment is swapped?
3. **Error Handling**: How to display CSRF errors in partial updates?

### Solution: Token Rotation on Re-render

**Pattern**:
1. POST endpoint validates CSRF token
2. On validation failure → Return form fragment with NEW token
3. On success → Return success fragment (no form, no token needed)
4. On business logic error → Return form fragment with NEW token

**Example: Registration Error Flow**

```python
@router.post("/auth/register")
async def register(
    request: Request,
    csrf_protect: CsrfProtect = Depends(),
    email: str = Form(...),
    password: str = Form(...),
    # ... other params ...
):
    # Validate CSRF token
    try:
        await csrf_protect.validate_csrf(request)
    except CsrfProtectError:
        # CSRF validation failed - return form with NEW token
        csrf_token, signed_token = csrf_protect.generate_csrf_tokens()
        response = templates.TemplateResponse(
            request=request,
            name="fragments/register_form.html",
            context={
                "csrf_token": csrf_token,
                "errors": {"general": "Security validation failed. Please try again."},
            },
            status_code=403,
        )
        csrf_protect.set_csrf_cookie(signed_token, response)
        return response

    # Validate password match
    if confirm_password and password != confirm_password:
        # Business logic error - return form with NEW token
        csrf_token, signed_token = csrf_protect.generate_csrf_tokens()
        response = templates.TemplateResponse(
            request=request,
            name="fragments/register_form.html",
            context={
                "csrf_token": csrf_token,  # ← NEW token
                "errors": {"password": "Passwords do not match"},
                "email": email,
                "display_name": display_name,
            },
            status_code=400,
        )
        csrf_protect.set_csrf_cookie(signed_token, response)  # ← NEW cookie
        return response

    # ... rest of logic ...
```

### HTMX-Specific Considerations

#### 1. Response Headers

HTMX respects `Set-Cookie` headers in partial responses:

```python
# ✅ HTMX will update cookie even on partial swap
response.headers["Set-Cookie"] = "csrf_token=...; Path=/; SameSite=Strict"
```

#### 2. Token in Form vs. Token in Header

**Option A: Form field (recommended for forms)**
```html
<form hx-post="/auth/login">
    <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
    <!-- form fields -->
</form>
```

**Option B: HTTP header (for JavaScript-initiated requests)**
```javascript
// Not needed for standard forms, but useful for fetch() calls
htmx.ajax('POST', '/api/endpoint', {
    headers: {
        'X-CSRF-Token': getCsrfToken()  // Read from cookie
    }
});
```

**Selflytics uses Option A** (form field) for all HTML forms.

#### 3. Error Fragment Template

Create `backend/app/templates/fragments/csrf_error.html`:

```html
{# CSRF validation error fragment #}
<div class="bg-red-50 border border-red-200 rounded-lg p-4" role="alert">
    <div class="flex items-center">
        <svg class="h-5 w-5 text-red-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"/>
        </svg>
        <div>
            <p class="text-red-800 text-sm font-medium">Security validation failed</p>
            <p class="text-red-600 text-xs mt-1">Please refresh the page and try again.</p>
        </div>
    </div>
</div>
```

---

## User Journeys

### Journey 1: Successful Login (Protected)

**Actor**: Legitimate User
**Goal**: Log into Selflytics account

```
┌────────────┐          ┌─────────────┐          ┌──────────────┐
│   User     │          │   Browser   │          │   Backend    │
└─────┬──────┘          └──────┬──────┘          └──────┬───────┘
      │                        │                         │
      │ Click "Login"          │                         │
      ├───────────────────────>│                         │
      │                        │ GET /login              │
      │                        ├────────────────────────>│
      │                        │                         │ Generate CSRF token
      │                        │                         │ csrf = "a3f8b2c..."
      │                        │                         ├──────┐
      │                        │ 200 OK                  │      │
      │                        │ Set-Cookie: csrf_token  │<─────┘
      │                        │ HTML form with token    │
      │                        │<────────────────────────┤
      │                        │                         │
      │  View login form       │                         │
      │<───────────────────────┤                         │
      │  (Token in hidden      │                         │
      │   field, invisible)    │                         │
      │                        │                         │
      │ Enter credentials      │                         │
      │ email: user@test.com   │                         │
      │ password: ********     │                         │
      │                        │                         │
      │ Click "Login" button   │                         │
      ├───────────────────────>│                         │
      │                        │ POST /auth/login        │
      │                        │ Cookie: csrf_token=...  │
      │                        │ Body:                   │
      │                        │   username=user@...     │
      │                        │   password=...          │
      │                        │   csrf_token=a3f8b2c... │
      │                        ├────────────────────────>│
      │                        │                         │ 1. Validate CSRF
      │                        │                         │    ✅ Cookie matches body
      │                        │                         │
      │                        │                         │ 2. Verify credentials
      │                        │                         │    ✅ Password correct
      │                        │                         │
      │                        │                         │ 3. Create JWT
      │                        │                         │    token = "eyJ0..."
      │                        │                         ├──────┐
      │                        │ 200 OK                  │      │
      │                        │ HX-Redirect: /dashboard │<─────┘
      │                        │ Set-Cookie: access_token│
      │                        │<────────────────────────┤
      │                        │                         │
      │                        │ GET /dashboard          │
      │                        │ Cookie: access_token    │
      │                        ├────────────────────────>│
      │                        │                         │
      │  View dashboard        │ 200 OK (HTML)           │
      │<───────────────────────┤<────────────────────────┤
      │  ✅ LOGGED IN          │                         │
```

**Key Observations**:
- ✅ CSRF token generated on GET request
- ✅ Token sent in both cookie and form body
- ✅ Backend validates token before processing credentials
- ✅ User experience unchanged (token is invisible)

---

### Journey 2: CSRF Attack Blocked (Garmin Link)

**Actor**: Attacker (via malicious website)
**Goal**: Link attacker's Garmin account to victim's Selflytics account
**Outcome**: Attack BLOCKED by CSRF protection

```
┌────────────┐   ┌─────────────┐   ┌──────────────┐   ┌──────────────┐
│   Victim   │   │  evil.com   │   │   Browser    │   │   Backend    │
└─────┬──────┘   └──────┬──────┘   └──────┬───────┘   └──────┬───────┘
      │                 │                  │                  │
      │ Logged into     │                  │                  │
      │ Selflytics      │                  │                  │
      │ (has auth       │                  │                  │
      │  cookie)        │                  │                  │
      │                 │                  │                  │
      │ Click phishing  │                  │                  │
      │ link in email   │                  │                  │
      ├────────────────>│                  │                  │
      │                 │ GET /malicious   │                  │
      │                 │<─────────────────┤                  │
      │                 │                  │                  │
      │                 │ 200 OK           │                  │
      │                 │ HTML with        │                  │
      │                 │ hidden form      │                  │
      │                 ├─────────────────>│                  │
      │                 │                  │                  │
      │                 │  <form action="https://selflytics  │
      │                 │   .app/garmin/link" method="POST"> │
      │                 │    <input name="username"          │
      │                 │     value="attacker@evil.com">     │
      │                 │    <input name="password"          │
      │                 │     value="attacker-pass">         │
      │                 │    <!-- ❌ NO csrf_token -->       │
      │                 │  </form>                           │
      │                 │                  │                  │
      │                 │ Auto-submit form │                  │
      │                 │ (JavaScript)     │                  │
      │                 ├─────────────────>│                  │
      │                 │                  │                  │
      │                 │                  │ POST /garmin/link│
      │                 │                  │ Cookie:          │
      │                 │                  │   access_token=  │
      │                 │                  │   (victim's JWT) │
      │                 │                  │ Body:            │
      │                 │                  │   username=...   │
      │                 │                  │   password=...   │
      │                 │                  │   csrf_token=    │
      │                 │                  │   (MISSING!)     │
      │                 │                  ├─────────────────>│
      │                 │                  │                  │ 1. Validate CSRF
      │                 │                  │                  │    ❌ Token missing!
      │                 │                  │                  │
      │                 │                  │                  │ 2. Reject request
      │                 │                  │                  ├──────┐
      │                 │                  │ 403 Forbidden    │      │
      │                 │                  │ CSRF validation  │<─────┘
      │                 │                  │ failed           │
      │                 │                  │<─────────────────┤
      │                 │                  │                  │
      │                 │  ❌ ATTACK BLOCKED                  │
      │                 │  Garmin account NOT linked          │
```

**Key Observations**:
- ❌ Attacker cannot obtain victim's CSRF token (same-origin policy)
- ❌ Attacker cannot set CSRF cookie for selflytics.app from evil.com
- ✅ Request rejected with 403 Forbidden
- ✅ Victim's account remains secure

**Why attacker cannot bypass**:
1. **Cannot read cookie**: Browser same-origin policy prevents evil.com from reading selflytics.app cookies
2. **Cannot set cookie**: Browser prevents evil.com from setting cookies for selflytics.app domain
3. **Cannot get token from page**: Attacker never saw the legitimate form, so has no token value
4. **Cannot guess token**: Token is cryptographically random (32+ bytes of entropy)

---

### Journey 3: Form Validation Error (Token Refresh)

**Actor**: Legitimate User
**Scenario**: User makes typo in password confirmation
**Goal**: Demonstrate CSRF token rotation on error

```
┌────────────┐          ┌─────────────┐          ┌──────────────┐
│   User     │          │   Browser   │          │   Backend    │
└─────┬──────┘          └──────┬──────┘          └──────┬───────┘
      │                        │                         │
      │ GET /register          │                         │
      │                        ├────────────────────────>│
      │                        │                         │ Generate token #1
      │                        │                         │ token1 = "abc123..."
      │                        │ 200 OK + token1         │
      │                        │<────────────────────────┤
      │                        │                         │
      │ Fill form:             │                         │
      │  email: user@test.com  │                         │
      │  password: Pass123     │                         │
      │  confirm: Pass124      │  ← TYPO!                │
      │                        │                         │
      │ Submit form            │                         │
      ├───────────────────────>│                         │
      │                        │ POST /auth/register     │
      │                        │ csrf_token=abc123...    │
      │                        ├────────────────────────>│
      │                        │                         │ 1. Validate CSRF
      │                        │                         │    ✅ Token valid
      │                        │                         │
      │                        │                         │ 2. Validate business
      │                        │                         │    ❌ Passwords mismatch
      │                        │                         │
      │                        │                         │ 3. Generate NEW token
      │                        │                         │    token2 = "xyz789..."
      │                        │                         │
      │                        │ 400 Bad Request         │
      │                        │ Form fragment with:     │
      │                        │  - Error message        │
      │                        │  - token2 (NEW!)        │
      │                        │  - Pre-filled email     │
      │                        │<────────────────────────┤
      │                        │                         │
      │ View error:            │  ← HTMX swaps form      │
      │  "Passwords do not     │     with new token      │
      │   match"               │                         │
      │                        │                         │
      │ Fix typo:              │                         │
      │  confirm: Pass123      │  ✅ Correct now         │
      │                        │                         │
      │ Submit again           │                         │
      ├───────────────────────>│                         │
      │                        │ POST /auth/register     │
      │                        │ csrf_token=xyz789...    │  ← NEW token
      │                        ├────────────────────────>│
      │                        │                         │ 1. Validate CSRF
      │                        │                         │    ✅ Token valid
      │                        │                         │
      │                        │                         │ 2. Create user
      │                        │                         │    ✅ Success!
      │                        │                         │
      │                        │ 200 OK + JWT cookie     │
      │                        │ HX-Redirect: /dashboard │
      │                        │<────────────────────────┤
      │                        │                         │
      │  ✅ REGISTERED         │                         │
```

**Key Observations**:
- ✅ CSRF token validated on first submission (typo in confirm password)
- ✅ New token generated when returning error form
- ✅ HTMX swaps form fragment with new token
- ✅ Second submission uses new token
- ✅ User unaware of token rotation (seamless UX)

---

### Journey 4: Token Expiration (Edge Case)

**Actor**: Legitimate User
**Scenario**: User leaves form open for > 1 hour (token expires)
**Goal**: Demonstrate graceful handling of expired token

```
┌────────────┐          ┌─────────────┐          ┌──────────────┐
│   User     │          │   Browser   │          │   Backend    │
└─────┬──────┘          └──────┬──────┘          └──────┬───────┘
      │                        │                         │
      │ GET /login             │                         │
      │                        ├────────────────────────>│
      │                        │                         │ Generate token
      │                        │                         │ expires_at = now+1h
      │                        │ 200 OK + token          │
      │                        │<────────────────────────┤
      │                        │                         │
      │ Fill email field       │                         │
      │ email: user@test.com   │                         │
      │                        │                         │
      ⏱️  USER GOES TO LUNCH   ⏱️                        ⏱️
      ⏱️  (1.5 hours pass)     ⏱️                        ⏱️
      │                        │                         │
      │ Return from lunch      │                         │
      │ Enter password         │                         │
      │ password: ********     │                         │
      │                        │                         │
      │ Submit form            │                         │
      ├───────────────────────>│                         │
      │                        │ POST /auth/login        │
      │                        │ csrf_token=<expired>    │
      │                        ├────────────────────────>│
      │                        │                         │ 1. Validate CSRF
      │                        │                         │    ❌ Token expired!
      │                        │                         │
      │                        │                         │ 2. Generate NEW token
      │                        │                         │    (Don't reveal why)
      │                        │                         │
      │                        │ 403 Forbidden           │
      │                        │ Form fragment with:     │
      │                        │  - "Please try again"   │
      │                        │  - NEW token            │
      │                        │  - Email preserved      │
      │                        │<────────────────────────┤
      │                        │                         │
      │ View message:          │                         │
      │  "Security validation  │                         │
      │   failed. Please try   │                         │
      │   again."              │                         │
      │                        │                         │
      │ Re-enter password      │                         │
      │ password: ********     │                         │
      │                        │                         │
      │ Submit again           │                         │
      ├───────────────────────>│                         │
      │                        │ POST /auth/login        │
      │                        │ csrf_token=<new>        │  ← Fresh token
      │                        ├────────────────────────>│
      │                        │                         │ 1. Validate CSRF
      │                        │                         │    ✅ Token valid
      │                        │                         │
      │                        │ 200 OK + JWT            │
      │                        │<────────────────────────┤
      │                        │                         │
      │  ✅ LOGGED IN          │                         │
```

**Key Observations**:
- ⏱️ CSRF tokens expire after 1 hour (configurable)
- ❌ Expired token rejected (prevents replay attacks)
- ✅ New token issued automatically on error
- ℹ️ Generic error message (don't reveal token expiration to potential attacker)
- ✅ User data preserved (email field) - good UX

---

## Testing Requirements

### Unit Tests

**Location**: `backend/tests/unit/test_csrf.py`

```python
"""Unit tests for CSRF protection."""

import pytest
from fastapi_csrf_protect import CsrfProtect


def test_csrf_token_generation():
    """Test that CSRF tokens are generated correctly."""
    csrf_protect = CsrfProtect()
    token1, signed1 = csrf_protect.generate_csrf_tokens()
    token2, signed2 = csrf_protect.generate_csrf_tokens()

    # Tokens should be unique
    assert token1 != token2
    assert signed1 != signed2

    # Tokens should have sufficient entropy (min 32 chars)
    assert len(token1) >= 32
    assert len(signed1) >= 32


def test_csrf_token_validation_success(csrf_protect):
    """Test successful CSRF token validation."""
    # Generate token
    token, signed_token = csrf_protect.generate_csrf_tokens()

    # Mock request with matching cookie and form field
    request = MockRequest(
        cookies={"csrf_token": signed_token},
        form={"csrf_token": token},
    )

    # Should not raise exception
    csrf_protect.validate_csrf(request)


def test_csrf_token_validation_missing_cookie(csrf_protect):
    """Test CSRF validation fails when cookie is missing."""
    token, _ = csrf_protect.generate_csrf_tokens()

    request = MockRequest(
        cookies={},  # No cookie!
        form={"csrf_token": token},
    )

    with pytest.raises(CsrfProtectError):
        csrf_protect.validate_csrf(request)


def test_csrf_token_validation_missing_form_field(csrf_protect):
    """Test CSRF validation fails when form field is missing."""
    _, signed_token = csrf_protect.generate_csrf_tokens()

    request = MockRequest(
        cookies={"csrf_token": signed_token},
        form={},  # No form field!
    )

    with pytest.raises(CsrfProtectError):
        csrf_protect.validate_csrf(request)


def test_csrf_token_validation_mismatch(csrf_protect):
    """Test CSRF validation fails when tokens don't match."""
    token1, signed1 = csrf_protect.generate_csrf_tokens()
    token2, signed2 = csrf_protect.generate_csrf_tokens()

    request = MockRequest(
        cookies={"csrf_token": signed1},
        form={"csrf_token": token2},  # Different token!
    )

    with pytest.raises(CsrfProtectError):
        csrf_protect.validate_csrf(request)
```

### Integration Tests

**Location**: `backend/tests/integration/test_csrf_routes.py`

```python
"""Integration tests for CSRF protection on routes."""

import pytest
from fastapi.testclient import TestClient


def test_register_requires_csrf_token(client: TestClient):
    """Test that /auth/register rejects requests without CSRF token."""
    response = client.post(
        "/auth/register",
        data={
            "email": "test@example.com",
            "password": "TestPass123",
            "display_name": "Test User",
            "confirm_password": "TestPass123",
            # csrf_token intentionally omitted
        },
    )

    assert response.status_code == 403
    assert "CSRF" in response.text or "Security validation" in response.text


def test_register_with_valid_csrf_token(client: TestClient):
    """Test that /auth/register accepts valid CSRF token."""
    # Get form with CSRF token
    form_response = client.get("/register")
    assert form_response.status_code == 200

    # Extract CSRF token from cookie
    csrf_cookie = form_response.cookies.get("csrf_token")

    # Extract CSRF token from HTML (parse hidden input)
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(form_response.text, "html.parser")
    csrf_token = soup.find("input", {"name": "csrf_token"})["value"]

    # Submit form with valid token
    response = client.post(
        "/auth/register",
        data={
            "email": "test@example.com",
            "password": "TestPass123",
            "display_name": "Test User",
            "confirm_password": "TestPass123",
            "csrf_token": csrf_token,
        },
        cookies={"csrf_token": csrf_cookie},
    )

    assert response.status_code == 200


def test_garmin_link_csrf_protection(authenticated_client: TestClient):
    """Test that /garmin/link is protected by CSRF."""
    # Attempt to link Garmin without CSRF token
    response = authenticated_client.post(
        "/garmin/link",
        data={
            "username": "test@garmin.com",
            "password": "GarminPass123",
            # csrf_token intentionally omitted
        },
    )

    assert response.status_code == 403


def test_csrf_token_rotation_on_error(client: TestClient):
    """Test that CSRF token is rotated when form has validation errors."""
    # Get initial form
    form1 = client.get("/register")
    token1 = form1.cookies.get("csrf_token")

    # Submit with password mismatch error
    response = client.post(
        "/auth/register",
        data={
            "email": "test@example.com",
            "password": "Pass123",
            "confirm_password": "Pass456",  # Mismatch!
            "csrf_token": extract_csrf_from_html(form1.text),
        },
        cookies={"csrf_token": token1},
        headers={"HX-Request": "true"},
    )

    assert response.status_code == 400
    assert "Passwords do not match" in response.text

    # Token should be rotated
    token2 = response.cookies.get("csrf_token")
    assert token2 is not None
    assert token2 != token1  # Different token!

    # Extract new token from returned form fragment
    new_csrf_token = extract_csrf_from_html(response.text)
    assert new_csrf_token != extract_csrf_from_html(form1.text)
```

### E2E Tests (Playwright)

**Location**: `backend/tests/e2e_playwright/test_csrf_e2e.py`

```python
"""E2E tests for CSRF protection."""

import pytest
from playwright.sync_api import Page, expect


def test_csrf_protects_against_cross_origin_post(page: Page, base_url: str):
    """Test that cross-origin POST requests are blocked."""

    # 1. User logs into Selflytics
    page.goto(f"{base_url}/login")
    page.fill('input[name="username"]', "test@example.com")
    page.fill('input[name="password"]', "TestPass123")
    page.click('button[type="submit"]')
    expect(page).to_have_url(f"{base_url}/dashboard")

    # 2. Simulate attacker's malicious page
    malicious_html = f"""
    <html>
    <body onload="document.forms[0].submit()">
        <form action="{base_url}/garmin/link" method="POST">
            <input name="username" value="attacker@evil.com">
            <input name="password" value="AttackerPass123">
        </form>
    </body>
    </html>
    """

    # Navigate to malicious page (simulates user clicking phishing link)
    page.set_content(malicious_html)

    # Wait for form submission to complete
    page.wait_for_load_state("networkidle")

    # 3. Verify attack was blocked
    # Navigate back to Selflytics to check Garmin link status
    page.goto(f"{base_url}/garmin/link")

    # Verify no Garmin account is linked
    expect(page.locator('[data-testid="form-link-garmin"]')).to_be_visible()
    # Attack was blocked - form is still showing (not success message)


def test_legitimate_garmin_link_with_csrf(
    page: Page,
    base_url: str,
    authenticated_page: Page,
):
    """Test that legitimate Garmin link works with CSRF protection."""

    # Navigate to Garmin link page
    authenticated_page.goto(f"{base_url}/garmin/link")

    # Fill form (CSRF token is automatically included in form)
    authenticated_page.fill('[data-testid="input-garmin-username"]', "test@garmin.com")
    authenticated_page.fill('[data-testid="input-garmin-password"]', "GarminPass123")

    # Submit form
    authenticated_page.click('[data-testid="submit-link-garmin"]')

    # Verify success
    expect(authenticated_page.locator("text=Successfully linked")).to_be_visible()


def test_csrf_token_visible_in_html(page: Page, base_url: str):
    """Test that CSRF tokens are present in form HTML."""
    page.goto(f"{base_url}/register")

    # Verify hidden input field exists
    csrf_input = page.locator('input[name="csrf_token"]')
    expect(csrf_input).to_be_hidden()  # Should be hidden from user
    expect(csrf_input).to_have_attribute("type", "hidden")

    # Verify token has value
    token_value = csrf_input.get_attribute("value")
    assert token_value is not None
    assert len(token_value) >= 32  # Sufficient entropy
```

### Manual Testing Checklist

Add to `docs/development/MANUAL_TESTING_RUNSHEET.md`:

```markdown
## CSRF Protection Testing

### Test 1: Verify CSRF tokens in forms
- [ ] Navigate to /register
- [ ] Open browser DevTools → Elements
- [ ] Verify `<input type="hidden" name="csrf_token">` exists
- [ ] Verify token value is non-empty (32+ characters)
- [ ] Check Application → Cookies → `csrf_token` cookie exists

### Test 2: Verify CSRF protection blocks forged requests
- [ ] Log into Selflytics
- [ ] Open new tab
- [ ] Create HTML file with forged form (see attack scenario 1)
- [ ] Open HTML file in browser
- [ ] Verify request is blocked (403 error or no action taken)

### Test 3: Verify legitimate requests still work
- [ ] Fill out registration form completely
- [ ] Submit form
- [ ] Verify account is created successfully
- [ ] Repeat for login, Garmin link

### Test 4: Verify token rotation on errors
- [ ] Fill registration form with password mismatch
- [ ] Submit form
- [ ] Open DevTools → Network → Find POST request
- [ ] Verify response includes new csrf_token cookie
- [ ] Verify response HTML includes new token in hidden field
- [ ] Correct password and submit
- [ ] Verify success

### Test 5: Verify HTMX compatibility
- [ ] Submit login form (uses HTMX)
- [ ] Verify HTMX swaps form fragment on error
- [ ] Verify CSRF token is preserved in swapped content
- [ ] Verify no full page reload occurs
```

---

## References

### Standards & Best Practices

- **OWASP CSRF Prevention Cheat Sheet**: https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html
- **OWASP Top 10 (2021)**: A01:2021 – Broken Access Control
- **CWE-352**: Cross-Site Request Forgery (CSRF)

### Libraries & Documentation

- **fastapi-csrf-protect**: https://github.com/aekasitt/fastapi-csrf-protect
- **FastAPI Security**: https://fastapi.tiangolo.com/tutorial/security/
- **HTMX Security**: https://htmx.org/docs/#security

### Project-Specific

- **Issue #8**: Add CSRF protection to all POST forms
- **PR #7 Review Feedback**: Original identification of CSRF vulnerability
- **backend/app/routes/auth.py**: Authentication routes requiring protection
- **backend/app/routes/garmin.py**: Garmin integration routes requiring protection

### Related Security Mechanisms

- **SameSite Cookies**: Provides partial CSRF protection (insufficient alone)
- **CORS (Cross-Origin Resource Sharing)**: Prevents cross-origin reads, NOT writes
- **JWT Authentication**: Selflytics uses JWTs in cookies (vulnerable without CSRF protection)

---

## Implementation Checklist

Copied from Issue #8 for convenience:

### Dependencies
- [ ] Add `fastapi-csrf-protect` package: `uv add fastapi-csrf-protect`

### Backend Configuration
- [ ] Add CSRF settings class with secret key from environment
- [ ] Configure `CsrfProtect.load_config` decorator
- [ ] Add exception handler for `CsrfProtectError`

### Route Protection
- [ ] `/auth/register` (backend/app/routes/auth.py)
- [ ] `/auth/login` (backend/app/routes/auth.py)
- [ ] `/garmin/link` (backend/app/routes/garmin.py)
- [ ] `/garmin/sync` (backend/app/routes/garmin.py) - added to scope

### Template Updates
- [ ] `backend/app/templates/fragments/register_form.html`
- [ ] `backend/app/templates/fragments/login_form.html`
- [ ] `backend/app/templates/fragments/garmin_link_form.html`
- [ ] Create `backend/app/templates/fragments/csrf_error.html`

### GET Route Updates (Token Generation)
- [ ] `/register` - Generate and pass CSRF token
- [ ] `/login` - Generate and pass CSRF token
- [ ] `/garmin/link` - Generate and pass CSRF token

### Testing
- [ ] Unit tests: Token generation, validation, expiration
- [ ] Integration tests: All protected routes
- [ ] E2E tests: HTMX compatibility, attack prevention
- [ ] Manual testing: Cross-origin attack simulation

### Security Validation
- [ ] Verify CSRF tokens are unique per session
- [ ] Verify CSRF tokens expire appropriately (1 hour)
- [ ] Verify CSRF protection doesn't break legitimate requests
- [ ] Test that POST requests without CSRF token are rejected with 403

### Documentation
- [ ] Update `docs/DEVELOPMENT_WORKFLOW.md` with CSRF testing guidelines
- [ ] Add environment variable for CSRF secret key to `.env.example`

---

**End of Specification**
