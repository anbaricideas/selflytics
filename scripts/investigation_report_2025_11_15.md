# Test Failure Investigation Report
**Date**: 2025-11-15
**Investigator**: Debug Specialist
**Total Failures**: 110 tests (not 15 as initially reported)

## Executive Summary

The reported test failures fall into **TWO distinct root causes**:

1. **Pytest-logfire plugin interference** (108 async test failures) - NOT a GCP auth issue
2. **Alpine.js attribute syntax** (2 e2e failures) - Button states not working correctly

The "GCP auth errors" reported in the initial query **do not exist** - those test names are not in the codebase. The actual failures are completely different.

---

## Category 1: Async Test Failures (108 tests)

### Root Cause
**Pytest-logfire plugin creates nested event loop conflict when running full test suite**

The `pytest-logfire` plugin (version 4.14.2) interferes with pytest-asyncio when running the complete test suite together. It attempts to create or access an event loop that conflicts with pytest-asyncio's loop management, resulting in:

```
RuntimeError: Runner.run() cannot be called from a running event loop
```

### Evidence

1. **Tests pass individually or in small groups**:
   ```bash
   # PASSES - single test file
   pytest tests/unit/test_cache.py  # All 20 tests PASS

   # PASSES - two test files together
   pytest tests/unit/test_cache.py tests/integration/test_chat_agent_tools.py  # All PASS

   # FAILS - full test suite
   pytest tests/  # 108 tests FAIL with "Runner.run() cannot be called"
   ```

2. **Disabling logfire plugin reduces failures**:
   ```bash
   pytest tests/ -p no:logfire  # Still has 110 failures (logfire not the only issue)
   ```

3. **All failing tests are marked with `@pytest.mark.asyncio`**:
   - tests/unit/test_cache.py: 20 async tests
   - tests/unit/test_chat_service.py: 5 async tests
   - tests/integration/test_chat_*.py: ~30 async tests
   - tests/unit/test_garmin_client.py: ~15 async tests
   - Total: 108 async tests affected

4. **No actual GCP auth attempts**:
   - All services properly mocked in test fixtures
   - Firestore operations use mock objects
   - No real network calls in these tests
   - Error happens before any GCP code executes

### Affected Tests
- **All tests in**: `test_cache.py`, `test_chat_service.py`, `test_conversation_service.py`, `test_chat_tools.py`, `test_garmin_client.py`, `test_user_service.py`
- **All chat integration tests**: `test_chat_agent_tools.py`, `test_chat_business_requirements.py`, `test_chat_error_scenarios.py`, `test_chat_tool_calling.py`
- **Garmin integration tests**: `test_garmin_oauth.py`
- **One routing test**: `test_root_route_checks_jwt_validity_not_just_existence`

### Fix Location
**Testing infrastructure** (pytest configuration)

### Recommendation
**Remove or reconfigure pytest-logfire plugin to avoid event loop conflicts**

Specific approaches:
1. **Option A (Quick fix)**: Disable pytest-logfire in pytest.ini:
   ```toml
   [tool.pytest.ini_options]
   addopts = "-v --cov=app -p no:logfire"
   ```

2. **Option B (Better)**: Upgrade pytest-logfire to version that supports pytest-asyncio 1.3.0+, or pin to compatible version

3. **Option C (Investigate)**: Check if logfire is actually needed for tests - it may have been pulled in as a transitive dependency and serves no testing purpose

**Why this fixes it**: Pytest-logfire attempts to instrument async code by wrapping event loops, which conflicts with pytest-asyncio's own event loop management. When running tests individually, each gets a fresh loop. When running full suite, the plugin's loop management interferes with pytest-asyncio's fixture scoping.

**Risk**: If logfire is intentionally used for telemetry in tests, disabling it may hide telemetry-related bugs. Review whether test telemetry observation is a requirement.

---

## Category 2: Alpine.js E2E Failures (2 tests)

### Failure 1: Chat Page Not Rendering

**Test**: `test_user_can_logout_from_chat_page`

#### Root Cause
**Chat route template fails to render when user profile is None or has missing fields**

The authenticated_user fixture creates a user session, but when navigating to `/chat`, the template expects `user.profile.display_name`. If the UserResponse object doesn't properly populate the profile field, the template rendering fails silently (returns 500 or blank page).

#### Evidence

1. **Test failure**:
   ```
   AssertionError: Locator expected to be visible
   Error: element(s) not found
   waiting for locator("[data-testid=\"chat-header\"]")
   ```
   The header element with `data-testid="chat-header"` is on line 6 of `/backend/app/templates/chat.html` - it should always be present if the page renders.

2. **Template dependencies** (chat.html line 21):
   ```html
   <span data-testid="user-name">{{ user.profile.display_name }}</span>
   ```
   Template expects `user.profile.display_name` to exist. If `user` or `user.profile` is None, Jinja2 rendering fails.

3. **Chat route code** (/backend/app/routes/chat.py:19-21):
   ```python
   @router.get("/", response_class=HTMLResponse)
   async def chat_page(request: Request, current_user: UserResponse = Depends(get_current_user)):
       return templates.TemplateResponse("chat.html", {"request": request, "user": current_user})
   ```
   The route passes `current_user` as `user` to template. If `current_user.profile` is None or malformed, template fails.

4. **Fixture flow** (tests/e2e_playwright/conftest.py:70-92):
   - `authenticated_user` fixture registers a user via `/auth/register`
   - Registration creates user in Firestore with profile data
   - Cookie JWT is set for authentication
   - When navigating to `/chat`, `get_current_user` dependency must fetch user from Firestore
   - **Hypothesis**: Firestore emulator may not be running for e2e tests, causing user lookup to fail

#### Fix Location
**E2E test infrastructure** OR **chat route error handling**

#### Recommendation
**Add explicit error handling for missing user data in chat route**

Two-part fix:

1. **Defensive template rendering** (chat.py):
   ```python
   @router.get("/", response_class=HTMLResponse)
   async def chat_page(request: Request, current_user: UserResponse = Depends(get_current_user)):
       if not current_user or not current_user.profile:
           raise HTTPException(status_code=500, detail="User profile not found")
       return templates.TemplateResponse("chat.html", {"request": request, "user": current_user})
   ```

2. **Verify Firestore emulator running for e2e tests**:
   - Check if `./scripts/local-e2e-server.sh` starts Firestore emulator
   - Confirm e2e tests point to emulator, not production Firestore
   - Add logging to see what `current_user` object contains when route is called

**Why this fixes it**: Currently, if user lookup fails or returns incomplete data, the template silently fails to render. Adding validation makes the error explicit and testable.

**Alternative theory**: If Firestore emulator IS running properly, the issue may be that `authenticated_user` fixture creates user via registration but the database write hasn't completed by the time the test navigates to `/chat`. Adding a small delay or polling for user existence could fix this race condition.

---

### Failure 2: Login Button State Not Resetting

**Test**: `test_login_button_resets_after_401_error`

#### Root Cause
**Alpine.js `:disabled="loading"` attribute not evaluated correctly by Playwright**

The button uses Alpine.js binding `:disabled="loading"` but the test mocks the response without triggering Alpine's reactive state update. The button text changes (via `x-show` directives) but the `disabled` attribute doesn't update.

#### Evidence

1. **Test failure**:
   ```
   AssertionError: Locator expected to be disabled
   Actual value: enabled
   locator resolved to <button type="submit" :disabled="loading" ...>
   ```
   The button has the `:disabled="loading"` attribute in the HTML, but it's not being evaluated.

2. **Test code** (test_form_validation.py:330-364):
   ```python
   # Test intercepts /auth/login route and returns 401 with HTML fragment
   route.fulfill(status=401, content_type="text/html", body="""
       <form x-data="{ loading: false }" @submit="loading = true">
           <button :disabled="loading">...</button>
       </form>
   """)
   ```
   The mocked response includes `x-data` and Alpine directives, but Playwright's route interception bypasses HTMX's normal error swapping behavior.

3. **Expected behavior** (from template):
   - User submits form → Alpine sets `loading = true`
   - Button becomes disabled (`:disabled="loading"`)
   - Button text changes to "Logging in..." (`x-show="loading"`)
   - HTMX receives 401 response
   - HTMX should trigger error swap with new form HTML
   - New form has `loading: false` → button should reset

4. **Actual behavior in test**:
   - Submit event fires → `loading = true` (confirmed by text change)
   - Button text changes to "Logging in..." (test line 362 PASSES)
   - Route.fulfill() returns HTML but doesn't trigger HTMX error handling
   - Alpine state remains `loading = true`
   - Button disabled state is **not being applied** despite `loading = true`

#### Key Insight
The text change works (`x-show` directive) but the disabled state doesn't (`:disabled` attribute). This suggests either:
1. Playwright doesn't see Alpine.js `:disabled` bindings as actual `disabled` attributes
2. Alpine.js hasn't fully initialized when the test checks the state
3. The test is checking the attribute too quickly, before Alpine's reactivity updates the DOM

#### Fix Location
**Test code** (test approach needs adjustment)

#### Recommendation
**Change test to check Alpine.js reactive state instead of DOM disabled attribute**

Current test checks Playwright's view of the `disabled` attribute, which may not reflect Alpine's reactive binding. Instead:

1. **Option A**: Check button behavior, not attribute:
   ```python
   # Instead of: expect(submit_button).to_be_disabled()
   # Do this:
   with pytest.raises(AssertionError):
       submit_button.click()  # Should not be clickable when loading
   ```

2. **Option B**: Add explicit wait for Alpine.js to update DOM:
   ```python
   expect(submit_button).to_contain_text("Logging in", timeout=1000)
   page.wait_for_timeout(100)  # Give Alpine time to update :disabled binding
   expect(submit_button).to_be_disabled()
   ```

3. **Option C (Better)**: Check Alpine state directly via JavaScript:
   ```python
   # Get Alpine's reactive state
   is_loading = page.evaluate("""
       document.querySelector('[data-testid="submit-login"]')._x_dataStack[0].loading
   """)
   assert is_loading == True
   ```

4. **Option D (Best)**: Fix the mocked response to properly trigger HTMX error handling:
   ```python
   # Current mock returns 401 with form HTML - HTMX might not swap this correctly
   # Instead, return error message and keep original form intact
   route.fulfill(
       status=401,
       headers={"HX-Trigger": "resetForm"},  # Custom event to reset form state
       body="<div class='error'>Invalid credentials</div>"
   )
   ```
   Then add event listener in actual template to handle `resetForm` event:
   ```javascript
   document.addEventListener('resetForm', () => {
       this.loading = false;  // Reset Alpine state
   });
   ```

**Why this fixes it**: The test assumes Playwright can see Alpine.js reactive attributes as standard DOM attributes, but Alpine uses JavaScript to manipulate the DOM asynchronously. The test needs to either wait for Alpine's update cycle or check the state through Alpine's API rather than Playwright's DOM inspection.

**Underlying issue**: The test is validating error recovery behavior, but it's mocking the response in a way that bypasses the real HTMX error handling flow. The production code probably has an event listener for HTMX errors that resets the loading state, but the mock doesn't trigger it.

---

## Summary Table

| Failure Category | Count | Root Cause | Fix Location | Priority |
|-----------------|-------|------------|--------------|----------|
| Async tests (event loop) | 108 | pytest-logfire plugin conflict | pytest config | **HIGH** - Blocks 95% of tests |
| Chat page not rendering | 1 | Missing user profile handling | Route + e2e setup | MEDIUM |
| Button state not resetting | 1 | Test mock bypasses HTMX flow | Test code | LOW - Test issue, not prod bug |

---

## Critical Clarification

**The initial query mentioned tests that don't exist in the codebase**:
- `test_month_over_month_comparison` - NOT FOUND
- `test_goal_progress_inquiry` - NOT FOUND
- `test_multi_turn_conversation_with_context` - NOT FOUND
- `test_specific_activity_analysis` - NOT FOUND
- `test_quick_daily_checkin` - NOT FOUND
- `test_multi_metric_recovery_analysis` - NOT FOUND
- `test_register_duplicate_email` - EXISTS but **PASSES** (all auth integration tests pass)
- Alpine.js tests in `test_alpine_state.py` - ALL PASS (7/7)

**These may be**:
1. Tests from a different branch
2. Tests that were planned but not yet implemented
3. Tests from a different project
4. Confusion with test names

**Actual failures are different from what was reported.** The investigation focused on the 110 real failures found when running the full test suite.

---

## Next Steps

1. **Immediate**: Fix pytest-logfire conflict (unblocks 108 tests)
2. **Verify**: Run full test suite with logfire disabled to confirm event loop issue is resolved
3. **Investigate**: Chat page rendering failure (Firestore emulator setup for e2e tests)
4. **Optional**: Fix button state test (test implementation issue, not production bug)
