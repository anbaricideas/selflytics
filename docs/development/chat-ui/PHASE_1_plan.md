# Phase 1: Core Backend Routes

**Phase**: 1 of 4
**Branch**: `feat/chat-ui-phase-1` (from `feat/chat-ui`)
**Status**: ⏳ NEXT
**Estimated Time**: 1-2 hours
**Dependencies**: None (foundation phase)
**Parallelizable**: No (Phases 2 and 3 depend on this)

---

## Goal

Establish the routing foundation for the chat-first navigation model by redirecting authenticated users to `/chat` instead of `/dashboard`, and repurposing `/dashboard` as a redirect to the new `/settings` hub page.

**Key Deliverables**:
- Root route (`/`) redirects to `/chat` for authenticated users
- `/dashboard` redirects to `/settings` (301 permanent)
- New `/settings` route created (authentication required)
- All route changes covered by integration tests

---

## Prerequisites

**Previous Phases**: None (foundation phase)

**Required Spec Context**:
- Lines 137-146: URL Routing Changes table
- Lines 378-396: Backend Route Changes
- Lines 417-422: Dashboard redirect implementation

**Current Implementation**:
- Root route redirects to `/dashboard` (main.py line 172)
- Dashboard route serves `dashboard.html` (dashboard.py line 14-28)
- No `/settings` route exists yet

---

## Implementation Steps

### Setup

- [ ] ⏳ NEXT: Create branch `feat/chat-ui-phase-1` from `feat/chat-ui`
  ```bash
  git checkout feat/chat-ui
  git pull
  git checkout -b feat/chat-ui-phase-1
  ```

---

### Step 1: Root Route Redirect Change

**File**: `backend/app/main.py`

**Current Implementation** (lines 150-177):
```python
@app.get("/")
async def root(request: Request) -> RedirectResponse:
    """Root endpoint - redirect based on authentication status.

    - Authenticated users → /dashboard
    - Unauthenticated users → /login
    """
    # ... token verification logic ...
    try:
        verify_token(token)
        return RedirectResponse(url="/dashboard", status_code=303)  # ← CHANGE THIS
    except ValueError:
        # ...
```

#### Unit Tests

- [ ] Write test: `test_root_redirects_to_chat_when_authenticated()`
  - Location: `backend/tests/integration/test_chat_ui_routes.py` (new file)
  - Test: Authenticated user visiting `/` redirects to `/chat`
  - Expected: Status 303, Location header = `/chat`

- [ ] Write test: `test_root_redirects_to_login_when_unauthenticated()`
  - Test: Unauthenticated user visiting `/` redirects to `/login`
  - Expected: Status 303, Location header = `/login` (no change from current)

- [ ] Verify tests fail (no implementation changes yet)
  ```bash
  uv --directory backend run pytest tests/integration/test_chat_ui_routes.py::test_root_redirects_to_chat_when_authenticated -v
  ```

#### Implementation

- [ ] Update root route redirect destination
  - Change line 172: `return RedirectResponse(url="/chat", status_code=303)`
  - Update docstring: "Authenticated users → /chat"
  - Spec reference: SPECIFICATION.md lines 139, 378-396

- [ ] Verify tests pass
  ```bash
  uv --directory backend run pytest tests/integration/test_chat_ui_routes.py -v
  ```

- [ ] Commit: "feat(chat-ui): redirect root to /chat instead of /dashboard"

---

### Step 2: Dashboard Redirect to Settings

**File**: `backend/app/routes/dashboard.py`

**Current Implementation** (lines 14-28):
```python
@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    user: UserResponse = Depends(get_current_user),
    templates=Depends(get_templates),
) -> HTMLResponse:
    """Display dashboard with welcome message and feature cards."""
    return templates.TemplateResponse(...)
```

#### Integration Tests

- [ ] Write test: `test_dashboard_redirects_to_settings_permanently()`
  - Location: `backend/tests/integration/test_chat_ui_routes.py`
  - Test: GET `/dashboard` returns 301 redirect to `/settings`
  - Expected: Status 301 (permanent), Location = `/settings`

- [ ] Write test: `test_old_dashboard_url_preserves_authentication_requirement()`
  - Test: Unauthenticated user accessing `/dashboard` → redirects to login
  - Expected: Authentication still required before redirect

- [ ] Verify tests fail
  ```bash
  uv --directory backend run pytest tests/integration/test_chat_ui_routes.py::test_dashboard_redirects_to_settings_permanently -v
  ```

#### Implementation

- [ ] Replace dashboard route with redirect
  - Replace entire function with redirect logic
  - Use 301 status (permanent redirect for SEO)
  - Spec reference: SPECIFICATION.md lines 140, 417-422

  ```python
  @router.get("/dashboard")
  async def dashboard_redirect():
      """Redirect old dashboard URL to new settings page."""
      return RedirectResponse("/settings", status_code=301)
  ```

- [ ] Verify tests pass
  ```bash
  uv --directory backend run pytest tests/integration/test_chat_ui_routes.py -v
  ```

- [ ] Commit: "feat(chat-ui): redirect /dashboard to /settings permanently"

---

### Step 3: New Settings Route

**File**: `backend/app/routes/dashboard.py`

#### Integration Tests

- [ ] Write test: `test_settings_route_requires_authentication()`
  - Location: `backend/tests/integration/test_chat_ui_routes.py`
  - Test: Unauthenticated user accessing `/settings` → redirects to login
  - Expected: 401 or redirect to `/login`

- [ ] Write test: `test_settings_route_renders_for_authenticated_user()`
  - Test: Authenticated user accesses `/settings`
  - Expected: Status 200, returns HTML response
  - Mock template rendering (template created in Phase 2)

- [ ] Write test: `test_settings_route_passes_user_context_to_template()`
  - Test: Settings route provides `user` in template context
  - Expected: Context includes `user` with `garmin_linked` status

- [ ] Verify tests fail
  ```bash
  uv --directory backend run pytest tests/integration/test_chat_ui_routes.py -k settings -v
  ```

#### Implementation

- [ ] Add new settings route
  - Add after dashboard redirect
  - Require authentication with `get_current_user` dependency
  - Template name: `settings.html` (created in Phase 2)
  - Spec reference: SPECIFICATION.md lines 142, 400-414

  ```python
  @router.get("/settings", response_class=HTMLResponse)
  async def settings_page(
      request: Request,
      user: UserResponse = Depends(get_current_user),
      templates=Depends(get_templates),
  ) -> HTMLResponse:
      """Settings hub page with Garmin and profile management links."""
      return templates.TemplateResponse(
          request=request,
          name="settings.html",
          context={"user": user},
      )
  ```

- [ ] Verify tests pass
  ```bash
  uv --directory backend run pytest tests/integration/test_chat_ui_routes.py -v
  ```

- [ ] Commit: "feat(chat-ui): add /settings hub route"

---

### Step 4: Update Existing Route Tests

**Files**: Various test files that reference dashboard routing

#### Test Updates

- [ ] Identify tests referencing `/dashboard` redirect
  ```bash
  grep -r "dashboard" backend/tests/integration/test_*.py
  ```

- [ ] Update affected tests:
  - `test_root_url_routing.py`: Update expectations for root route
  - Any authentication flow tests that expect dashboard redirect
  - Change expected redirect from `/dashboard` to `/chat`

- [ ] Run full integration test suite
  ```bash
  uv --directory backend run pytest tests/integration -v
  ```

- [ ] Fix any failures caused by routing changes

- [ ] Commit: "test(chat-ui): update route tests for chat-first navigation"

---

### Final Validation

#### Test Verification

- [ ] Run full test suite (unit + integration)
  ```bash
  uv --directory backend run pytest tests/ -v --cov=app
  ```

- [ ] Verify 80%+ coverage maintained
  ```bash
  uv --directory backend run pytest tests/ --cov=app --cov-report=term-missing
  ```

- [ ] Check coverage on modified files specifically:
  - `app/main.py` (root route)
  - `app/routes/dashboard.py` (redirects and settings)

#### Code Quality

- [ ] Run linter
  ```bash
  uv run ruff check .
  ```

- [ ] Run formatter
  ```bash
  uv run ruff format --check .
  ```

- [ ] Fix any issues
  ```bash
  uv run ruff format .
  uv run ruff check --fix .
  ```

- [ ] Run security scan
  ```bash
  uv run bandit -c backend/pyproject.toml -r backend/app/ -ll
  ```

#### Git Workflow

- [ ] Verify all changes committed
  ```bash
  git status
  ```

- [ ] Push branch to origin
  ```bash
  git push -u origin feat/chat-ui-phase-1
  ```

- [ ] Create PR targeting `feat/chat-ui` (NOT main)
  ```bash
  gh pr create --base feat/chat-ui --title "Phase 1: Core Backend Routes" --body "
  ## Summary
  Implements chat-first navigation routing:
  - Root route redirects to /chat (not /dashboard)
  - /dashboard redirects to /settings permanently (301)
  - New /settings route created (authentication required)

  ## Tests
  - All route changes covered by integration tests
  - Full test suite passing
  - 80%+ coverage maintained

  ## Spec Reference
  SPECIFICATION.md lines 137-146, 378-422
  "
  ```

- [ ] Update this plan: Mark all steps ✅ DONE
- [ ] Update ROADMAP.md: Phase 1 status → ✅ DONE

---

## Testing Requirements

### Integration Tests

**New Test File**: `backend/tests/integration/test_chat_ui_routes.py`

**Test Coverage**:
- Root route redirects to `/chat` when authenticated
- Root route redirects to `/login` when unauthenticated
- `/dashboard` redirects to `/settings` permanently (301)
- `/settings` requires authentication
- `/settings` renders template with user context
- Unauthenticated access to `/settings` redirects to login

**Test Patterns** (from existing tests):
```python
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_root_redirects_to_chat_when_authenticated(test_user_token):
    """Authenticated user visiting / should redirect to /chat."""
    response = client.get(
        "/",
        cookies={"access_token": f"Bearer {test_user_token}"}
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/chat"
```

### Coverage Goal

- **Target**: 100% coverage on modified routes
- **Minimum**: 80% overall coverage maintained

---

## Success Criteria

### Technical Validation

- [ ] Root route redirects authenticated users to `/chat`
- [ ] Root route redirects unauthenticated users to `/login`
- [ ] `/dashboard` permanently redirects to `/settings` (301)
- [ ] `/settings` route exists and requires authentication
- [ ] `/settings` provides user context to template

### Test Validation

- [ ] All new integration tests passing
- [ ] All existing tests updated and passing
- [ ] 80%+ coverage maintained
- [ ] No regressions in authentication flows

### Code Quality

- [ ] Ruff linter passes
- [ ] Ruff formatter passes
- [ ] Bandit security scan passes
- [ ] No f-strings in logger calls

### Git Validation

- [ ] Branch created from `feat/chat-ui` (verified)
- [ ] PR targets `feat/chat-ui` (NOT main)
- [ ] All commits follow conventional commit format
- [ ] Clear commit messages referencing spec

---

## Notes

### Design Decisions

**Why 301 for dashboard redirect?**
- Permanent redirect signals to search engines and browsers that `/dashboard` is permanently moved
- Allows browsers to cache the redirect
- Spec explicitly requires 301 (line 140)

**Why separate settings route instead of renaming dashboard?**
- Clean separation of concerns
- Allows old URL to redirect gracefully
- Easier to track analytics on both URLs
- Spec requires both routes to exist (line 140, 142)

### Spec References

- **Root route change**: Lines 139, 378-396
- **Dashboard redirect**: Lines 140, 417-422
- **Settings route**: Lines 142, 400-414

### Common Patterns

**Redirect pattern**:
```python
return RedirectResponse("/target", status_code=301)  # Permanent
return RedirectResponse("/target", status_code=303)  # Temporary (POST-redirect-GET)
```

**Authentication requirement**:
```python
user: UserResponse = Depends(get_current_user)  # Raises 401 if not authenticated
```

---

## Dependencies for Next Phase

**Phase 2 (Settings Hub Page) requires**:
- [ ] `/settings` route exists and functional (this phase)
- [ ] Route passes `user` context to template (this phase)
- Template rendering mocked in tests (Phase 2 creates actual template)

**Phase 3 (Chat Banner) depends on**:
- [ ] Root route redirects to `/chat` (this phase)
- This ensures users land on chat page where banner appears

**Phase 4 (Cleanup) depends on**:
- [ ] All routing changes in place (this phase)
- Tests updated to reflect new navigation (this phase)

---

## Session Summary Template

```markdown
### Session [Date/Time]

**Completed**:
- [ ] Steps completed this session
- [ ] Tests written and passing
- [ ] Commits made

**Blockers**: None / [Description]

**Next Session**: Continue from step [X]
```

---

*Last Updated: 2025-11-15*
*Status: Ready to Start - ⏳ NEXT*
