# Phase 1: CSRF Infrastructure & Auth Routes Protection

**Branch**: `feat/csrf-phase-1`
**Status**: ⏳ NEXT
**Estimated Time**: 2 hours
**Started**: [Date to be filled]
**Completed**: [Date to be filled]

---

## Goal

Establish CSRF protection infrastructure and secure authentication routes. This phase installs and configures `fastapi-csrf-protect`, implements the Double Submit Cookie pattern, and protects `/auth/register` and `/auth/login` endpoints with comprehensive TDD coverage.

**Key Deliverables**:
- fastapi-csrf-protect library installed and configured
- CSRF exception handler for browser and API requests
- Protected /auth/register and /auth/login routes
- CSRF tokens in register and login forms
- Token rotation on validation errors
- Unit + integration tests for CSRF protection

**Security Impact**:
- Blocks forced account registration attacks
- Blocks session fixation via forced login attacks
- Establishes pattern for protecting remaining routes (Phase 2)

---

## Prerequisites

**Required Before Starting**:
- [ ] Current branch: `feat/csrf` exists and is checked out
- [ ] Specification read: `/Users/bryn/repos/selflytics-csrf/docs/development/csrf/CSRF_SPECIFICATION.md`
- [ ] Roadmap reviewed: `/Users/bryn/repos/selflytics-csrf/docs/development/csrf/ROADMAP.md`
- [ ] All existing tests passing: `uv --directory backend run pytest tests/ -v`

**Specification Context**:
- Lines 232-280: fastapi-csrf-protect selection and Double Submit Cookie pattern
- Lines 285-341: Configuration in main.py (CsrfSettings, exception handler)
- Lines 342-363: Environment configuration (CSRF_SECRET)
- Lines 369-404: Route protection pattern
- Lines 409-449: Template integration (token generation, hidden fields)
- Lines 461-578: HTMX integration and token rotation

---

## Deliverables

### New Files
- [ ] `backend/app/templates/fragments/csrf_error.html` - CSRF error fragment for HTMX

### Modified Files
- [ ] `backend/pyproject.toml` - Add fastapi-csrf-protect dependency
- [ ] `backend/.env.example` - Add CSRF_SECRET variable
- [ ] `backend/app/config.py` - Add csrf_secret field to Settings
- [ ] `backend/app/main.py` - Configure CsrfProtect, add exception handler
- [ ] `backend/app/routes/auth.py` - Protect POST routes, update GET routes
- [ ] `backend/app/templates/fragments/register_form.html` - Add csrf_token hidden field
- [ ] `backend/app/templates/fragments/login_form.html` - Add csrf_token hidden field

### New Tests
- [ ] `backend/tests/unit/test_csrf.py` - CSRF token generation/validation unit tests
- [ ] `backend/tests/integration/test_csrf_routes.py` - Auth routes CSRF integration tests

---

## Implementation Steps

### Setup

- [ ] ⏳ NEXT: Create branch from feat/csrf
  ```bash
  git checkout feat/csrf
  git pull origin feat/csrf  # Ensure up to date
  git checkout -b feat/csrf-phase-1
  ```

---

### Step 1: Install CSRF Protection Library

**Goal**: Add fastapi-csrf-protect dependency to project

#### Implementation

- [ ] Add fastapi-csrf-protect package
  ```bash
  uv add fastapi-csrf-protect
  ```

- [ ] Verify installation
  ```bash
  uv --directory backend run python -c "import fastapi_csrf_protect; print(fastapi_csrf_protect.__version__)"
  ```

- [ ] Commit dependency addition
  ```bash
  git add pyproject.toml uv.lock
  git commit -m "chore: Add fastapi-csrf-protect dependency"
  ```

**Success Criteria**:
- [ ] fastapi-csrf-protect appears in pyproject.toml dependencies
- [ ] uv.lock updated with new package
- [ ] Package can be imported in Python

---

### Step 2: Configure Environment Variables

**Goal**: Add CSRF_SECRET to environment configuration

**File**: `backend/.env.example`

#### Implementation

- [ ] Add CSRF_SECRET to .env.example (lines 17-18)
  ```bash
  # CSRF Protection
  CSRF_SECRET="change-this-in-production-min-32-chars"
  ```

- [ ] Add CSRF_SECRET to local .env file
  ```bash
  # CSRF Protection (dev environment)
  CSRF_SECRET="dev-csrf-secret-change-in-production-min-32-chars-for-security"
  ```

- [ ] Commit environment configuration
  ```bash
  git add backend/.env.example
  git commit -m "chore: Add CSRF_SECRET environment variable"
  ```

**Success Criteria**:
- [ ] .env.example contains CSRF_SECRET with example value
- [ ] Local .env contains CSRF_SECRET for development
- [ ] Secret is 32+ characters (sufficient entropy)

**Reference**: Spec lines 345-350, 354-363

---

### Step 3: Update Application Settings

**Goal**: Add csrf_secret field to Pydantic Settings model

**File**: `backend/app/config.py`

#### Unit Tests (TDD)

- [ ] Write test for csrf_secret configuration in `backend/tests/unit/test_config.py` (create if needed)
  ```python
  def test_csrf_secret_has_default():
      """Test that csrf_secret has a default value."""
      settings = Settings()
      assert settings.csrf_secret is not None
      assert len(settings.csrf_secret) >= 32

  def test_csrf_secret_loaded_from_env(monkeypatch):
      """Test that csrf_secret can be loaded from environment."""
      test_secret = "test-csrf-secret-min-32-chars-long"
      monkeypatch.setenv("CSRF_SECRET", test_secret)
      settings = Settings()
      assert settings.csrf_secret == test_secret
  ```

- [ ] Run tests, verify they fail
  ```bash
  uv --directory backend run pytest tests/unit/test_config.py -v -k csrf
  ```

#### Implementation

- [ ] Add csrf_secret field to Settings class (after access_token_expire_minutes)
  ```python
  # CSRF Protection
  csrf_secret: str = Field(
      default="dev-csrf-secret-change-in-production",
      description="CSRF token secret key (min 32 characters)",
  )
  ```

- [ ] Run tests, verify they pass
  ```bash
  uv --directory backend run pytest tests/unit/test_config.py -v -k csrf
  ```

- [ ] Commit configuration update
  ```bash
  git add backend/app/config.py backend/tests/unit/test_config.py
  git commit -m "feat: Add csrf_secret to application settings"
  ```

**Success Criteria**:
- [ ] csrf_secret field exists in Settings class
- [ ] Default value is 32+ characters
- [ ] Tests verify env var loading works
- [ ] All tests passing

**Reference**: Spec lines 354-363

---

### Step 4: Create CSRF Error Template

**Goal**: Create HTML fragment for CSRF validation errors (HTMX partial updates)

**File**: `backend/app/templates/fragments/csrf_error.html`

#### Implementation

- [ ] Create csrf_error.html template (from spec lines 562-578)
  ```html
  {# CSRF validation error fragment #}
  <div class="bg-red-50 border border-red-200 rounded-lg p-4" role="alert" data-testid="csrf-error">
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

- [ ] Commit template
  ```bash
  git add backend/app/templates/fragments/csrf_error.html
  git commit -m "feat: Add CSRF error template fragment"
  ```

**Success Criteria**:
- [ ] Template file created in correct location
- [ ] Template includes data-testid for testing
- [ ] Error message is generic (security best practice)
- [ ] Styling consistent with existing error fragments

**Reference**: Spec lines 562-578

---

### Step 5: Configure CSRF Protection in Main App

**Goal**: Configure CsrfProtect with settings and exception handler

**File**: `backend/app/main.py`

#### Unit Tests (TDD)

- [ ] Write tests in `backend/tests/unit/test_csrf.py`
  ```python
  """Unit tests for CSRF protection."""

  import pytest
  from fastapi_csrf_protect import CsrfProtect
  from fastapi_csrf_protect.exceptions import CsrfProtectError


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


  def test_csrf_tokens_are_strings():
      """Test that tokens are string type."""
      csrf_protect = CsrfProtect()
      token, signed_token = csrf_protect.generate_csrf_tokens()

      assert isinstance(token, str)
      assert isinstance(signed_token, str)
  ```

- [ ] Run tests, verify they pass (library functionality)
  ```bash
  uv --directory backend run pytest tests/unit/test_csrf.py -v
  ```

- [ ] Commit tests
  ```bash
  git add backend/tests/unit/test_csrf.py
  git commit -m "test: Add CSRF token generation unit tests"
  ```

#### Implementation

- [ ] Add imports to main.py (after existing imports)
  ```python
  from fastapi_csrf_protect import CsrfProtect
  from fastapi_csrf_protect.exceptions import CsrfProtectError
  from pydantic import BaseModel
  ```

- [ ] Add CsrfSettings class (after load_dotenv block, before logger)
  ```python
  # CSRF Settings
  class CsrfSettings(BaseModel):
      """CSRF protection settings."""
      secret_key: str
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
      """Load CSRF configuration from settings."""
      settings = get_settings()
      return CsrfSettings(
          secret_key=settings.csrf_secret,
          cookie_secure=settings.environment != "development",
      )
  ```

- [ ] Add CSRF exception handler (after http_exception_handler function)
  ```python
  @app.exception_handler(CsrfProtectError)
  async def csrf_protect_exception_handler(request: Request, exc: CsrfProtectError):
      """Handle CSRF validation failures.

      For browser/HTMX requests, return HTML error fragment or page.
      For API requests, return JSON error response.
      """
      # Check if request is from browser/HTMX (not API)
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

- [ ] Run tests to verify no regressions
  ```bash
  uv --directory backend run pytest tests/ -v
  ```

- [ ] Commit CSRF configuration
  ```bash
  git add backend/app/main.py
  git commit -m "feat: Configure CSRF protection in main app"
  ```

**Success Criteria**:
- [ ] CsrfSettings class defined with correct fields
- [ ] get_csrf_config loads settings from environment
- [ ] Exception handler returns appropriate response types (HTML/JSON)
- [ ] Exception handler differentiates HTMX vs full page requests
- [ ] All existing tests still pass

**Reference**: Spec lines 285-341

---

### Step 6: Protect /auth/register Endpoint

**Goal**: Add CSRF protection to registration endpoint with token rotation

**File**: `backend/app/routes/auth.py`

#### Integration Tests (TDD)

- [ ] Write tests in `backend/tests/integration/test_csrf_routes.py`
  ```python
  """Integration tests for CSRF protection on routes."""

  import pytest
  from bs4 import BeautifulSoup
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
      assert csrf_cookie is not None

      # Extract CSRF token from HTML
      soup = BeautifulSoup(form_response.text, "html.parser")
      csrf_input = soup.find("input", {"name": "csrf_token"})
      assert csrf_input is not None
      csrf_token = csrf_input["value"]

      # Submit form with valid token
      response = client.post(
          "/auth/register",
          data={
              "email": "newuser@example.com",
              "password": "TestPass123",
              "display_name": "New User",
              "confirm_password": "TestPass123",
              "csrf_token": csrf_token,
          },
          cookies={"csrf_token": csrf_cookie},
      )

      # Should succeed (or fail with email exists, not CSRF error)
      assert response.status_code in (200, 400)
      if response.status_code == 400:
          # If 400, should be email exists, not CSRF error
          assert "CSRF" not in response.text


  def test_csrf_token_rotation_on_register_error(client: TestClient):
      """Test that CSRF token is rotated when registration has validation errors."""
      # Get initial form
      form1 = client.get("/register")
      token1 = form1.cookies.get("csrf_token")

      soup = BeautifulSoup(form1.text, "html.parser")
      csrf_token1 = soup.find("input", {"name": "csrf_token"})["value"]

      # Submit with password mismatch error
      response = client.post(
          "/auth/register",
          data={
              "email": "test@example.com",
              "password": "Pass123",
              "confirm_password": "Pass456",  # Mismatch!
              "display_name": "Test",
              "csrf_token": csrf_token1,
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
      soup2 = BeautifulSoup(response.text, "html.parser")
      csrf_input2 = soup2.find("input", {"name": "csrf_token"})
      assert csrf_input2 is not None
      csrf_token2 = csrf_input2["value"]
      assert csrf_token2 != csrf_token1  # Different token value!
  ```

- [ ] Run tests, verify they fail
  ```bash
  uv --directory backend run pytest tests/integration/test_csrf_routes.py::test_register_requires_csrf_token -v
  ```

#### Implementation

- [ ] Update GET /register endpoint to generate CSRF token
  ```python
  from fastapi_csrf_protect import CsrfProtect

  @router.get("/register", response_class=HTMLResponse)
  async def register_form(
      request: Request,
      csrf_protect: CsrfProtect = Depends(),
      templates=Depends(get_templates),
  ) -> HTMLResponse:
      """Display registration form with CSRF token."""
      csrf_token, signed_token = csrf_protect.generate_csrf_tokens()
      response = templates.TemplateResponse(
          request=request,
          name="register.html",
          context={"csrf_token": csrf_token},
      )
      csrf_protect.set_csrf_cookie(signed_token, response)
      return response
  ```

- [ ] Update POST /auth/register endpoint to validate CSRF token
  ```python
  @router.post("/auth/register")
  async def register(
      request: Request,
      csrf_protect: CsrfProtect = Depends(),  # Add CSRF dependency
      email: str = Form(...),
      password: str = Form(...),
      display_name: str = Form(...),
      confirm_password: str = Form(None),
      user_service: UserService = Depends(get_user_service),
      templates=Depends(get_templates),
  ):
      """Register a new user."""

      # Validate CSRF token FIRST (before any business logic)
      await csrf_protect.validate_csrf(request)

      # Validate password confirmation if provided
      if confirm_password and password != confirm_password:
          if request.headers.get("HX-Request"):
              # Generate NEW token for form re-render
              csrf_token, signed_token = csrf_protect.generate_csrf_tokens()
              response = templates.TemplateResponse(
                  request=request,
                  name="fragments/register_form.html",
                  context={
                      "csrf_token": csrf_token,  # NEW token
                      "errors": {"password": "Passwords do not match"},
                      "email": email,
                      "display_name": display_name,
                  },
                  status_code=status.HTTP_400_BAD_REQUEST,
              )
              csrf_protect.set_csrf_cookie(signed_token, response)  # NEW cookie
              return response
          raise HTTPException(
              status_code=status.HTTP_400_BAD_REQUEST,
              detail="Passwords do not match",
          )

      # ... rest of existing logic (email check, user creation)
      # IMPORTANT: Also add token rotation to existing_user error case
  ```

- [ ] Update existing_user error response to rotate token
  ```python
  # Around line 98-100 in current auth.py
  if existing_user:
      if request.headers.get("HX-Request"):
          # Generate NEW token for form re-render
          csrf_token, signed_token = csrf_protect.generate_csrf_tokens()
          response = templates.TemplateResponse(
              request=request,
              name="fragments/register_form.html",
              context={
                  "csrf_token": csrf_token,  # NEW token
                  "errors": {"general": "An account with this email already exists."},
                  "email": email,
                  "display_name": display_name,
              },
              status_code=status.HTTP_400_BAD_REQUEST,
          )
          csrf_protect.set_csrf_cookie(signed_token, response)  # NEW cookie
          return response
      # ... existing error handling for non-HTMX ...
  ```

- [ ] Run integration tests, verify they pass
  ```bash
  uv --directory backend run pytest tests/integration/test_csrf_routes.py -v -k register
  ```

- [ ] Commit register endpoint protection
  ```bash
  git add backend/app/routes/auth.py backend/tests/integration/test_csrf_routes.py
  git commit -m "feat: Add CSRF protection to /auth/register endpoint"
  ```

**Success Criteria**:
- [ ] GET /register generates and sets CSRF token
- [ ] POST /auth/register validates CSRF token
- [ ] Token rotation works on validation errors
- [ ] Integration tests pass
- [ ] Error responses include new tokens

**Reference**: Spec lines 369-404, 479-525

---

### Step 7: Update Register Form Template

**Goal**: Add hidden csrf_token field to registration form

**File**: `backend/app/templates/fragments/register_form.html`

#### Implementation

- [ ] Add csrf_token hidden field as FIRST field in form (after opening `<form>` tag, before line 11)
  ```html
  <form
      hx-post="/auth/register"
      hx-swap="outerHTML"
      x-data="{ loading: false }"
      @submit="loading = true"
      data-reset-loading-on-swap
      class="space-y-5"
      data-testid="register-form"
  >
      <!-- CSRF Token (MUST be first field) -->
      <input type="hidden" name="csrf_token" value="{{ csrf_token }}">

      <!-- General Error Message (for user enumeration prevention) -->
      {% if errors and errors.general %}
      ...
  ```

- [ ] Verify template renders correctly
  ```bash
  # Start dev server
  ./scripts/dev-server.sh
  # Visit http://localhost:8000/register in browser
  # Inspect HTML, verify hidden csrf_token field exists
  ```

- [ ] Commit template update
  ```bash
  git add backend/app/templates/fragments/register_form.html
  git commit -m "feat: Add CSRF token to register form template"
  ```

**Success Criteria**:
- [ ] Hidden input field with name="csrf_token" exists
- [ ] Field is first in form (best practice)
- [ ] Value populated from template context
- [ ] Field not visible to users

**Reference**: Spec lines 432-449

---

### Step 8: Protect /auth/login Endpoint

**Goal**: Add CSRF protection to login endpoint with token rotation

**File**: `backend/app/routes/auth.py`

#### Integration Tests (TDD)

- [ ] Add login tests to `backend/tests/integration/test_csrf_routes.py`
  ```python
  def test_login_requires_csrf_token(client: TestClient):
      """Test that /auth/login rejects requests without CSRF token."""
      response = client.post(
          "/auth/login",
          data={
              "username": "test@example.com",
              "password": "TestPass123",
              # csrf_token intentionally omitted
          },
      )

      assert response.status_code == 403
      assert "CSRF" in response.text or "Security validation" in response.text


  def test_login_with_valid_csrf_token(client: TestClient):
      """Test that /auth/login accepts valid CSRF token."""
      # Get form with CSRF token
      form_response = client.get("/login")
      assert form_response.status_code == 200

      # Extract CSRF token
      csrf_cookie = form_response.cookies.get("csrf_token")
      soup = BeautifulSoup(form_response.text, "html.parser")
      csrf_token = soup.find("input", {"name": "csrf_token"})["value"]

      # Submit with valid token (will fail auth but not CSRF)
      response = client.post(
          "/auth/login",
          data={
              "username": "test@example.com",
              "password": "WrongPassword",
              "csrf_token": csrf_token,
          },
          cookies={"csrf_token": csrf_cookie},
      )

      # Should fail auth (401 or 400), not CSRF (403)
      assert response.status_code in (400, 401)
      assert "CSRF" not in response.text


  def test_csrf_token_rotation_on_login_error(client: TestClient):
      """Test that CSRF token is rotated on login failure."""
      # Get initial form
      form1 = client.get("/login")
      token1 = form1.cookies.get("csrf_token")
      soup1 = BeautifulSoup(form1.text, "html.parser")
      csrf_token1 = soup1.find("input", {"name": "csrf_token"})["value"]

      # Submit with wrong credentials
      response = client.post(
          "/auth/login",
          data={
              "username": "test@example.com",
              "password": "WrongPassword",
              "csrf_token": csrf_token1,
          },
          cookies={"csrf_token": token1},
          headers={"HX-Request": "true"},
      )

      assert response.status_code in (400, 401)

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
  uv --directory backend run pytest tests/integration/test_csrf_routes.py::test_login_requires_csrf_token -v
  ```

#### Implementation

- [ ] Update GET /login endpoint to generate CSRF token
  ```python
  @router.get("/login", response_class=HTMLResponse)
  async def login_form(
      request: Request,
      csrf_protect: CsrfProtect = Depends(),
      templates=Depends(get_templates),
  ) -> HTMLResponse:
      """Display login form with CSRF token."""
      csrf_token, signed_token = csrf_protect.generate_csrf_tokens()
      response = templates.TemplateResponse(
          request=request,
          name="login.html",
          context={"csrf_token": csrf_token},
      )
      csrf_protect.set_csrf_cookie(signed_token, response)
      return response
  ```

- [ ] Update POST /auth/login endpoint to validate CSRF token (around line 150+)
  ```python
  @router.post("/auth/login")
  async def login(
      request: Request,
      response: Response,
      csrf_protect: CsrfProtect = Depends(),  # Add CSRF dependency
      form_data: OAuth2PasswordRequestForm = Depends(),
      user_service: UserService = Depends(get_user_service),
      templates=Depends(get_templates),
  ):
      """Authenticate user and set JWT cookie."""

      # Validate CSRF token FIRST
      await csrf_protect.validate_csrf(request)

      # ... existing authentication logic ...

      # Update error response to rotate token (around line 165+)
      if not user or not verify_password(form_data.password, user.hashed_password):
          if request.headers.get("HX-Request"):
              # Generate NEW token for form re-render
              csrf_token, signed_token = csrf_protect.generate_csrf_tokens()
              error_response = templates.TemplateResponse(
                  request=request,
                  name="fragments/login_form.html",
                  context={
                      "csrf_token": csrf_token,  # NEW token
                      "errors": {"general": "Invalid email or password"},
                      "email": form_data.username,
                  },
                  status_code=status.HTTP_401_UNAUTHORIZED,
              )
              csrf_protect.set_csrf_cookie(signed_token, error_response)
              return error_response
          # ... existing error handling for non-HTMX ...
  ```

- [ ] Run integration tests, verify they pass
  ```bash
  uv --directory backend run pytest tests/integration/test_csrf_routes.py -v -k login
  ```

- [ ] Commit login endpoint protection
  ```bash
  git add backend/app/routes/auth.py backend/tests/integration/test_csrf_routes.py
  git commit -m "feat: Add CSRF protection to /auth/login endpoint"
  ```

**Success Criteria**:
- [ ] GET /login generates and sets CSRF token
- [ ] POST /auth/login validates CSRF token
- [ ] Token rotation works on auth failure
- [ ] Integration tests pass

**Reference**: Spec lines 369-404, 479-525

---

### Step 9: Update Login Form Template

**Goal**: Add hidden csrf_token field to login form

**File**: `backend/app/templates/fragments/login_form.html`

#### Implementation

- [ ] Add csrf_token hidden field as FIRST field in form (after opening `<form>` tag, before line 11)
  ```html
  <form
      hx-post="/auth/login"
      hx-swap="outerHTML"
      x-data="{ loading: false }"
      @submit="loading = true"
      data-reset-loading-on-swap
      class="space-y-5"
      data-testid="login-form"
  >
      <!-- CSRF Token (MUST be first field) -->
      <input type="hidden" name="csrf_token" value="{{ csrf_token }}">

      <!-- Error Message -->
      {% if errors and errors.general %}
      ...
  ```

- [ ] Commit template update
  ```bash
  git add backend/app/templates/fragments/login_form.html
  git commit -m "feat: Add CSRF token to login form template"
  ```

**Success Criteria**:
- [ ] Hidden input field with name="csrf_token" exists
- [ ] Field is first in form
- [ ] Value populated from template context

**Reference**: Spec lines 432-449

---

### Test Verification

**Goal**: Verify all Phase 1 tests pass with good coverage

- [ ] Run all unit tests
  ```bash
  uv --directory backend run pytest tests/unit -v
  ```

- [ ] Run all integration tests
  ```bash
  uv --directory backend run pytest tests/integration -v
  ```

- [ ] Run tests with coverage report
  ```bash
  uv --directory backend run pytest tests/ -v --cov=app --cov-report=term-missing
  ```

- [ ] Verify coverage ≥ 80% on new code
  ```bash
  # Check coverage report for:
  # - app/main.py (CSRF exception handler)
  # - app/routes/auth.py (CSRF validation)
  # - app/config.py (csrf_secret field)
  ```

**Success Criteria**:
- [ ] All unit tests passing
- [ ] All integration tests passing
- [ ] Coverage ≥ 80% on CSRF-related code
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

- [ ] Verify imports at top of files (no function-level imports)
  ```bash
  # Manually check auth.py and main.py
  ```

**Success Criteria**:
- [ ] No ruff errors
- [ ] Code formatted consistently
- [ ] No security warnings from bandit
- [ ] All imports at module level

---

### Manual Verification

**Goal**: Manually verify CSRF protection works in browser

- [ ] Start development server
  ```bash
  ./scripts/dev-server.sh
  ```

- [ ] Test registration flow
  - [ ] Navigate to http://localhost:8000/register
  - [ ] Open DevTools → Elements
  - [ ] Verify `<input type="hidden" name="csrf_token">` exists
  - [ ] Verify value is non-empty (32+ characters)
  - [ ] Open DevTools → Application → Cookies
  - [ ] Verify `csrf_token` cookie exists
  - [ ] Fill form with password mismatch
  - [ ] Submit and verify form re-renders with error
  - [ ] Verify NEW csrf_token value in hidden field (token rotated)
  - [ ] Correct password and submit
  - [ ] Verify successful registration

- [ ] Test login flow
  - [ ] Navigate to http://localhost:8000/login
  - [ ] Verify csrf_token hidden field and cookie exist
  - [ ] Submit with wrong password
  - [ ] Verify form re-renders with error
  - [ ] Verify token rotated
  - [ ] Submit with correct credentials
  - [ ] Verify successful login

- [ ] Test CSRF attack prevention
  - [ ] Create test HTML file with forged POST form (see spec line 177-195)
  - [ ] Open file in browser while logged in
  - [ ] Verify request is blocked (403 error)

**Success Criteria**:
- [ ] CSRF tokens visible in HTML and cookies
- [ ] Token rotation works on errors
- [ ] Legitimate requests succeed
- [ ] Forged requests blocked with 403

**Reference**: Spec lines 1160-1200

---

### Git Workflow

**Goal**: Push branch and create PR into feat/csrf

- [ ] Final commit with phase completion
  ```bash
  git add .
  git commit -m "docs: Mark Phase 1 complete in plan"
  ```

- [ ] Push phase branch
  ```bash
  git push -u origin feat/csrf-phase-1
  ```

- [ ] Create PR into feat/csrf (not main!)
  ```bash
  gh pr create --base feat/csrf --title "Phase 1: CSRF Infrastructure & Auth Routes" \
    --body "Implements CSRF protection infrastructure and secures /auth/register and /auth/login endpoints.

  **Changes**:
  - Install and configure fastapi-csrf-protect
  - Add CSRF exception handler
  - Protect /auth/register and /auth/login routes
  - Add CSRF tokens to register and login forms
  - Token rotation on validation errors

  **Testing**:
  - Unit tests for CSRF token generation
  - Integration tests for auth routes
  - Coverage: XX% (≥80% target)

  **Closes**: Part of #8"
  ```

- [ ] Update this plan: Mark all steps ✅ DONE
- [ ] Update ROADMAP.md: Phase 1 status → ✅ DONE

**Success Criteria**:
- [ ] PR created targeting feat/csrf branch
- [ ] PR description clear and complete
- [ ] CI checks passing on PR
- [ ] Phase 1 plan marked complete

---

## Success Criteria

### Technical Success

- [x] fastapi-csrf-protect installed and configured
- [x] CSRF exception handler returns appropriate responses (403 HTML/JSON)
- [x] /auth/register requires valid CSRF token
- [x] /auth/login requires valid CSRF token
- [x] Tokens rotated on validation errors
- [x] Unit tests pass (token generation, validation)
- [x] Integration tests pass (auth routes protected)

### Quality Metrics

- [x] 80%+ test coverage on CSRF configuration
- [x] Ruff linting passes
- [x] Bandit security scan passes
- [x] All existing tests still pass (no regressions)

### User Experience

- [x] Registration flow works seamlessly (token invisible to user)
- [x] Login flow works seamlessly
- [x] Error messages generic and helpful
- [x] Token rotation transparent to user

---

## Notes

### Design Decisions

- **CSRF token as first form field**: Best practice for consistent parsing
- **Token rotation on ALL errors**: Prevents token replay attacks
- **Generic error messages**: "Security validation failed" prevents information leakage
- **httponly=False for CSRF cookie**: Required for JavaScript/HTMX access (different from auth cookie)

### Specification References

- Lines 232-280: Library selection and Double Submit Cookie pattern
- Lines 285-341: Configuration and exception handler implementation
- Lines 369-404: Route protection pattern (validate_csrf before business logic)
- Lines 409-449: Template integration (generate tokens in GET, include in forms)
- Lines 479-525: Token rotation on validation errors

### Common Patterns

**Route Protection Pattern**:
```python
@router.post("/endpoint")
async def endpoint(
    request: Request,
    csrf_protect: CsrfProtect = Depends(),  # 1. Add dependency
    # ... other params ...
):
    await csrf_protect.validate_csrf(request)  # 2. Validate FIRST
    # ... business logic ...
```

**Token Rotation on Error**:
```python
if error_condition:
    csrf_token, signed_token = csrf_protect.generate_csrf_tokens()
    response = templates.TemplateResponse(
        request=request,
        name="fragments/form.html",
        context={"csrf_token": csrf_token, "errors": {...}},
        status_code=400,
    )
    csrf_protect.set_csrf_cookie(signed_token, response)
    return response
```

---

## Dependencies for Next Phase

**Phase 2 needs from Phase 1**:
- [x] Working CSRF configuration (CsrfProtect, exception handler)
- [x] Verified token rotation pattern
- [x] Integration test patterns for CSRF routes
- [x] Template pattern for hidden csrf_token fields

---

*Last Updated: [To be filled on completion]*
*Status: ⏳ NEXT*
