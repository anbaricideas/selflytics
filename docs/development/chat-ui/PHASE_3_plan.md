# Phase 3: Chat Banner & Dismissal Logic

**Phase**: 3 of 4
**Branch**: `feat/chat-ui-phase-3` (from `feat/chat-ui`)
**Status**: 📋 READY
**Estimated Time**: 1-2 hours
**Dependencies**: Phase 1 (root route redirects to chat)
**Parallelizable**: Yes (can work concurrently with Phase 2)

---

## Goal

Add a dismissible Garmin connection banner to the chat interface that appears for users with unlinked Garmin accounts. The banner provides a gentle reminder to link their account without being intrusive, using localStorage for dismissal persistence (cleared on login).

**Key Deliverables**:
- Garmin banner component in `chat.html`
- JavaScript dismissal logic with localStorage
- Login handler clears banner state
- Banner only appears when `user.garmin_linked == False`
- Mobile responsive banner layout

---

## Prerequisites

**Previous Phases**:
- Phase 1: Root route redirects to `/chat` ✅

**Required Spec Context**:
- Lines 149-200: Garmin Banner component specification
- Lines 461-494: Frontend Logic & State Management
- Lines 760-786: Banner JavaScript code snippets
- Lines 495-535: Mobile Responsiveness

**Current Implementation**:
- Chat page at `/chat/` with Alpine.js interface
- Logout handler at `/logout` clears cookie (auth.py line 225-238)
- No banner component exists yet
- No localStorage integration in logout

---

## Implementation Steps

### Setup

- [ ] ⏳ NEXT: Create branch `feat/chat-ui-phase-3` from `feat/chat-ui`
  ```bash
  git checkout feat/chat-ui
  git pull
  git checkout -b feat/chat-ui-phase-3
  ```

- [ ] Verify Phase 1 merged to `feat/chat-ui`
  ```bash
  git log feat/chat-ui --oneline | head -5
  ```

---

### Step 1: Banner Component (HTML/CSS)

**File**: `backend/app/templates/chat.html`

**Location**: Add banner before chat interface (after header, before sidebar/messages)

#### Integration Tests

- [ ] Write test: `test_banner_appears_when_garmin_not_linked()`
  - Location: `backend/tests/integration/test_chat_ui_templates.py`
  - Test: Chat page shows banner when `user.garmin_linked == False`
  - Expected: Banner div with id="garmin-banner" present in HTML

- [ ] Write test: `test_banner_absent_when_garmin_linked()`
  - Test: Chat page does not show banner when `user.garmin_linked == True`
  - Expected: Banner div not present in HTML (conditional rendering)

- [ ] Write test: `test_banner_has_link_to_garmin_oauth()`
  - Test: Banner includes "Link Now" button linking to `/garmin/link`
  - Expected: Link href="/garmin/link"

- [ ] Write test: `test_banner_has_dismiss_button()`
  - Test: Banner includes dismiss button with id="dismiss-banner"
  - Expected: Button with id and close icon

- [ ] Verify tests fail
  ```bash
  uv --directory backend run pytest tests/integration/test_chat_ui_templates.py -k banner -v
  ```

#### Implementation

- [ ] Add banner component after header in `chat.html`
  - Insert after line 34 (after header closing tag)
  - Conditional rendering with Jinja2 `{% if not user.garmin_linked %}`
  - Spec reference: SPECIFICATION.md lines 149-200

  ```html
  <!-- Garmin Connection Banner (only if not linked) -->
  {% if not user.garmin_linked %}
  <div id="garmin-banner" class="bg-blue-50 border-l-4 border-blue-400 p-4" data-testid="garmin-banner">
    <div class="flex items-center justify-between flex-wrap gap-4">
      <div class="flex items-center flex-1 min-w-0">
        <svg class="h-6 w-6 text-blue-400 mr-3 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20" aria-hidden="true">
          <!-- Link/chain icon -->
          <path fill-rule="evenodd" d="M12.586 4.586a2 2 0 112.828 2.828l-3 3a2 2 0 01-2.828 0 1 1 0 00-1.414 1.414 4 4 0 005.656 0l3-3a4 4 0 00-5.656-5.656l-1.5 1.5a1 1 0 101.414 1.414l1.5-1.5zm-5 5a2 2 0 012.828 0 1 1 0 101.414-1.414 4 4 0 00-5.656 0l-3 3a4 4 0 105.656 5.656l1.5-1.5a1 1 0 10-1.414-1.414l-1.5 1.5a2 2 0 11-2.828-2.828l3-3z" clip-rule="evenodd"/>
        </svg>
        <p class="text-sm text-blue-700">
          Connect your Garmin account to analyze your activity data with AI
        </p>
      </div>
      <div class="flex items-center gap-4 flex-shrink-0">
        <a href="/garmin/link"
           class="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 transition text-sm font-medium"
           data-testid="banner-link-now"
           aria-label="Link your Garmin account now">
          Link Now
        </a>
        <button id="dismiss-banner"
                class="text-blue-700 hover:text-blue-900 transition"
                data-testid="banner-dismiss"
                aria-label="Dismiss banner">
          <svg class="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
            <!-- Close/X icon -->
            <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"/>
          </svg>
        </button>
      </div>
    </div>
  </div>
  {% endif %}
  ```

- [ ] Add test selectors (data-testid attributes)
  - `garmin-banner`: Banner container
  - `banner-link-now`: Link Now button
  - `banner-dismiss`: Dismiss button

- [ ] Verify tests pass
  ```bash
  uv --directory backend run pytest tests/integration/test_chat_ui_templates.py -k banner -v
  ```

- [ ] Commit: "feat(chat-ui): add Garmin banner to chat page"

---

### Step 2: Banner Dismissal Logic (JavaScript)

**File**: `backend/app/templates/chat.html`

**Location**: Add script at end of template (before `{% endblock %}`)

#### Unit Tests

Note: JavaScript testing typically done via E2E tests. These integration tests verify the script is present.

- [ ] Write test: `test_banner_dismissal_script_included()`
  - Location: `backend/tests/integration/test_chat_ui_templates.py`
  - Test: Chat page includes banner dismissal script
  - Expected: HTML contains "garmin-banner-dismissed" string (localStorage key)

- [ ] Verify test fails
  ```bash
  uv --directory backend run pytest tests/integration/test_chat_ui_templates.py::test_banner_dismissal_script_included -v
  ```

#### Implementation

- [ ] Add banner dismissal script before `{% endblock %}`
  - After chatInterface() script
  - Check localStorage on page load
  - Handle dismiss button click
  - Spec reference: SPECIFICATION.md lines 178-200, 760-786

  ```html
  <script>
  // Banner dismissal logic (runs after DOM loads)
  document.addEventListener('DOMContentLoaded', () => {
    const banner = document.getElementById('garmin-banner');
    if (!banner) return; // Banner not present (already linked)

    // Check dismissed state from localStorage
    const dismissed = localStorage.getItem('garmin-banner-dismissed');
    if (dismissed === 'true') {
      banner.style.display = 'none';
    }

    // Handle dismiss button click
    const dismissBtn = document.getElementById('dismiss-banner');
    if (dismissBtn) {
      dismissBtn.addEventListener('click', () => {
        banner.style.display = 'none';
        localStorage.setItem('garmin-banner-dismissed', 'true');
      });
    }
  });
  </script>
  ```

- [ ] Verify script syntax valid
  ```bash
  # Manual verification: Check browser console for errors
  ./scripts/dev-server.sh
  # Open http://localhost:8000/chat/ in browser
  # Check Console tab for errors
  ```

- [ ] Verify test passes
  ```bash
  uv --directory backend run pytest tests/integration/test_chat_ui_templates.py::test_banner_dismissal_script_included -v
  ```

- [ ] Commit: "feat(chat-ui): add banner dismissal JavaScript logic"

---

### Step 3: Logout Handler Integration

**File**: `backend/app/templates/chat.html` and `backend/app/templates/base.html`

**Goal**: Clear banner dismissed state when user logs out

#### Integration Tests

- [ ] Write test: `test_logout_clears_localstorage_in_client()`
  - Location: `backend/tests/integration/test_chat_ui_templates.py`
  - Test: Logout button includes onclick handler to clear localStorage
  - Expected: Button has onclick with removeItem call

- [ ] Verify test fails
  ```bash
  uv --directory backend run pytest tests/integration/test_chat_ui_templates.py::test_logout_clears_localstorage_in_client -v
  ```

#### Implementation

- [ ] Add logout handler script to `chat.html`
  - Option 1: Add onclick to logout button directly
  - Option 2: Add event listener in script
  - Prefer Option 2 for separation of concerns
  - Spec reference: SPECIFICATION.md lines 195-199

  ```html
  <script>
  // Logout handler - clears banner state
  document.addEventListener('DOMContentLoaded', () => {
    const logoutForm = document.querySelector('form[action="/logout"]');
    if (logoutForm) {
      logoutForm.addEventListener('submit', () => {
        // Clear banner dismissed state before logout
        localStorage.removeItem('garmin-banner-dismissed');
      });
    }
  });
  </script>
  ```

- [ ] Consider adding to `base.html` instead for global logout handling
  - Benefit: Applies to all pages (dashboard, settings, chat)
  - Decision: Add to `base.html` if logout button in base, otherwise to `chat.html`

- [ ] Verify logout script location
  ```bash
  grep -n "logout" backend/app/templates/base.html
  grep -n "logout" backend/app/templates/chat.html
  ```

- [ ] Add script to appropriate template (chat.html has logout button)

- [ ] Verify test passes
  ```bash
  uv --directory backend run pytest tests/integration/test_chat_ui_templates.py::test_logout_clears_localstorage_in_client -v
  ```

- [ ] Commit: "feat(chat-ui): clear banner state on logout"

---

### Step 4: Mobile Responsive Banner

**File**: `backend/app/templates/chat.html`

#### Manual Testing

- [ ] Test mobile layout (viewport < 640px)
  - Banner elements stack vertically
  - "Link Now" button full width or prominent
  - Dismiss button accessible (not hidden)
  - Spec reference: SPECIFICATION.md lines 202-206, 524-529

- [ ] Test tablet/desktop layout (viewport ≥ 640px)
  - Banner displays in horizontal layout
  - Icon, message, and buttons aligned
  - Adequate spacing

#### Implementation

- [ ] Verify responsive flexbox classes in banner
  - `flex-wrap gap-4`: Allows wrapping on small screens
  - `flex-1 min-w-0`: Message area flexible, can shrink
  - `flex-shrink-0`: Buttons don't shrink

- [ ] Consider mobile-specific adjustments
  - Banner already uses `flex-wrap` for responsive behavior
  - Gap spacing (`gap-4`) provides mobile-friendly spacing
  - No additional mobile classes needed if current layout works

- [ ] Test in browser at various widths
  ```bash
  ./scripts/dev-server.sh
  # Open http://localhost:8000/chat/ in browser
  # Use DevTools responsive mode to test breakpoints
  # Test at: 320px (mobile), 768px (tablet), 1024px (desktop)
  ```

- [ ] Adjust if needed:
  - If buttons too wide on mobile, add `sm:w-auto w-full` to "Link Now" button
  - If icon hidden on small screens, verify `flex-shrink-0` on icon

- [ ] Commit: "feat(chat-ui): verify banner mobile responsiveness"

---

### Step 5: E2E Tests for Banner Flow

**File**: `backend/tests/e2e_playwright/test_chat_ui_navigation.py` (new file)

**Goal**: Test complete banner dismissal user journey

#### E2E Tests

- [ ] Write test: `test_user_can_dismiss_banner_and_it_stays_hidden()`
  - Test: User dismisses banner, refreshes page, banner stays hidden
  - Expected: Banner hidden after dismiss, persists across page refresh

- [ ] Write test: `test_banner_reappears_after_logout_and_login()`
  - Test: User dismisses banner, logs out, logs back in
  - Expected: Banner appears again after new login

- [ ] Write test: `test_banner_link_navigates_to_garmin_oauth()`
  - Test: Click "Link Now" navigates to `/garmin/link`
  - Expected: URL changes to `/garmin/link`

- [ ] Write test: `test_banner_does_not_appear_when_garmin_linked()`
  - Test: User with linked Garmin sees no banner
  - Expected: Banner element not present in DOM

- [ ] Verify tests fail (banner logic not fully tested yet)
  ```bash
  uv --directory backend run pytest tests/e2e_playwright/test_chat_ui_navigation.py -k banner -v
  ```

#### Implementation

- [ ] Create `test_chat_ui_navigation.py` E2E test file
  - Use authenticated_user fixture
  - Test banner visibility and dismissal
  - Test localStorage persistence

  ```python
  """E2E tests for chat UI navigation and banner interactions."""

  from playwright.async_api import Page, expect

  class TestGarminBanner:
      """Tests for Garmin connection banner on chat page."""

      async def test_user_can_dismiss_banner_and_it_stays_hidden(
          self, authenticated_user: Page, base_url: str
      ):
          """User can dismiss banner and it stays hidden on refresh."""
          # Navigate to chat
          await authenticated_user.goto(f"{base_url}/chat/")

          # Banner should be visible initially (test user has no Garmin linked)
          banner = authenticated_user.locator('[data-testid="garmin-banner"]')
          await expect(banner).to_be_visible(timeout=5000)

          # Dismiss banner
          dismiss_btn = authenticated_user.locator('[data-testid="banner-dismiss"]')
          await dismiss_btn.click()

          # Banner should be hidden
          await expect(banner).to_be_hidden()

          # Refresh page
          await authenticated_user.reload()

          # Banner should still be hidden
          await expect(banner).to_be_hidden(timeout=5000)

      async def test_banner_reappears_after_logout_and_login(
          self, page: Page, base_url: str
      ):
          """Banner reappears after user logs out and logs back in."""
          import time

          timestamp = int(time.time())
          email = f"banner-test-{timestamp}@example.com"
          password = "TestPass123!"

          # Register new user
          await page.goto(f"{base_url}/register")
          await page.fill('[data-testid="input-display-name"]', "Banner Test")
          await page.fill('[data-testid="input-email"]', email)
          await page.fill('[data-testid="input-password"]', password)
          await page.fill('[data-testid="input-confirm-password"]', password)
          await page.click('[data-testid="submit-register"]')

          # Should redirect to chat (Phase 1 routing)
          await page.wait_for_url(f"{base_url}/chat/", timeout=10000)

          # Banner should be visible
          banner = page.locator('[data-testid="garmin-banner"]')
          await expect(banner).to_be_visible()

          # Dismiss banner
          await page.click('[data-testid="banner-dismiss"]')
          await expect(banner).to_be_hidden()

          # Logout
          await page.click('[data-testid="logout-button"]')
          await page.wait_for_url(f"{base_url}/login", timeout=5000)

          # Login again
          await page.fill('input[name="username"]', email)
          await page.fill('input[name="password"]', password)
          await page.click('[data-testid="submit-login"]')

          # Should redirect back to chat
          await page.wait_for_url(f"{base_url}/chat/", timeout=10000)

          # Banner should be visible again
          await expect(banner).to_be_visible(timeout=5000)
  ```

- [ ] Run E2E tests locally
  ```bash
  ./scripts/local-e2e-server.sh  # Terminal 1
  uv --directory backend run pytest tests/e2e_playwright/test_chat_ui_navigation.py -v --headed  # Terminal 2
  ```

- [ ] Verify all E2E tests pass

- [ ] Commit: "test(chat-ui): add E2E tests for banner dismissal flow"

---

### Final Validation

#### Test Verification

- [ ] Run full integration test suite
  ```bash
  uv --directory backend run pytest tests/integration -v
  ```

- [ ] Run E2E tests locally
  ```bash
  ./scripts/local-e2e-server.sh  # Terminal 1
  uv --directory backend run pytest tests/e2e_playwright/test_chat_ui_navigation.py -v  # Terminal 2
  ```

- [ ] Verify 80%+ coverage maintained
  ```bash
  uv --directory backend run pytest tests/ --cov=app --cov-report=term-missing
  ```

#### Manual Verification

- [ ] Complete manual testing checklist:
  - [ ] Banner appears on chat page when Garmin not linked
  - [ ] Banner does NOT appear when Garmin linked
  - [ ] "Link Now" button navigates to `/garmin/link`
  - [ ] Dismiss button hides banner
  - [ ] Banner stays hidden after page refresh (same session)
  - [ ] Banner reappears after logout and login
  - [ ] Mobile: Banner elements stack/wrap appropriately
  - [ ] Desktop: Banner displays in single row

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

#### Git Workflow

- [ ] Verify all changes committed
  ```bash
  git status
  ```

- [ ] Push branch to origin
  ```bash
  git push -u origin feat/chat-ui-phase-3
  ```

- [ ] Create PR targeting `feat/chat-ui` (NOT main)
  ```bash
  gh pr create --base feat/chat-ui --title "Phase 3: Chat Banner & Dismissal Logic" --body "
  ## Summary
  Adds dismissible Garmin banner to chat interface:
  - Banner component with Link Now and dismiss buttons
  - JavaScript dismissal logic with localStorage
  - Logout handler clears banner state
  - Mobile responsive layout
  - E2E tests for complete user journey

  ## Tests
  - Integration tests for banner rendering
  - E2E tests for dismissal flow
  - Manual testing checklist completed
  - 80%+ coverage maintained

  ## Spec Reference
  SPECIFICATION.md lines 149-200, 461-494, 760-786
  "
  ```

- [ ] Update this plan: Mark all steps ✅ DONE
- [ ] Update ROADMAP.md: Phase 3 status → ✅ DONE

---

## Testing Requirements

### Integration Tests

**File**: `backend/tests/integration/test_chat_ui_templates.py`

**Test Coverage**:
- Banner appears when `user.garmin_linked == False`
- Banner absent when `user.garmin_linked == True`
- Banner has "Link Now" link to `/garmin/link`
- Banner has dismiss button with correct ID
- Banner dismissal script included in template
- Logout handler includes localStorage clear

### E2E Tests

**New Test File**: `backend/tests/e2e_playwright/test_chat_ui_navigation.py`

**Critical User Journeys**:
1. User dismisses banner → banner hidden → refresh page → banner stays hidden
2. User dismisses banner → logout → login → banner reappears
3. User clicks "Link Now" → navigates to Garmin OAuth
4. User with linked Garmin → banner not visible

**Test Patterns**:
```python
async def test_user_can_dismiss_banner_and_it_stays_hidden(
    authenticated_user: Page, base_url: str
):
    """User can dismiss banner and it stays hidden on refresh."""
    await authenticated_user.goto(f"{base_url}/chat/")
    banner = authenticated_user.locator('[data-testid="garmin-banner"]')
    await expect(banner).to_be_visible()

    # Dismiss
    await authenticated_user.click('[data-testid="banner-dismiss"]')
    await expect(banner).to_be_hidden()

    # Refresh
    await authenticated_user.reload()
    await expect(banner).to_be_hidden()
```

### Coverage Goal

- **Target**: 100% coverage on banner rendering logic
- **Minimum**: 80% overall coverage maintained

---

## Success Criteria

### Technical Validation

- [ ] Banner appears only when `user.garmin_linked == False`
- [ ] Banner dismissal hides banner via CSS (`display: none`)
- [ ] Dismissed state stored in localStorage (`garmin-banner-dismissed: "true"`)
- [ ] Banner stays hidden on page refresh (same session)
- [ ] Banner reappears after logout and login (localStorage cleared)
- [ ] "Link Now" button navigates to `/garmin/link`

### User Experience Validation

- [ ] Banner messaging clear and actionable
- [ ] Dismiss button easily accessible
- [ ] No layout shift when banner appears/disappears
- [ ] Mobile responsive (elements stack appropriately)

### Test Validation

- [ ] All integration tests passing
- [ ] All E2E tests passing locally
- [ ] Manual testing checklist completed
- [ ] 80%+ coverage maintained

### Code Quality

- [ ] Ruff linter passes
- [ ] Ruff formatter passes
- [ ] No console errors in browser
- [ ] JavaScript syntax valid

---

## Notes

### Design Decisions

**Why localStorage instead of backend flag?**
- Session-based dismissal (spec requirement, line 54)
- No server round-trip needed
- Lightweight (single boolean value)
- Clears automatically on logout (we handle this)

**Why "Link Now" instead of "Connect"?**
- Matches spec exactly (line 73, 169)
- Clear call-to-action
- Consistent with Garmin OAuth flow terminology

**Why dismissal doesn't persist across sessions?**
- Gentle reminder strategy (spec lines 54, 195-199)
- Ensures users don't forget to link account
- Not intrusive (one-click dismiss)

### Spec References

- **Banner component**: Lines 149-200
- **Dismissal logic**: Lines 178-200, 461-494
- **Logout integration**: Lines 195-199
- **Mobile responsive**: Lines 202-206, 524-529
- **Code snippets**: Lines 760-786

### Common Patterns

**localStorage API**:
```javascript
localStorage.setItem('key', 'value')  // Store
localStorage.getItem('key')           // Retrieve (returns string or null)
localStorage.removeItem('key')        // Delete
```

**Conditional rendering (Jinja2)**:
```html
{% if not user.garmin_linked %}
  <!-- Banner HTML -->
{% endif %}
```

**Event listener pattern**:
```javascript
document.addEventListener('DOMContentLoaded', () => {
  const element = document.getElementById('id');
  if (element) {
    element.addEventListener('click', () => {
      // Handler logic
    });
  }
});
```

---

## Dependencies for Next Phase

**Phase 4 (Cleanup) requires**:
- [ ] Banner functional and tested (this phase)
- [ ] Chat page routing established (Phase 1)
- [ ] E2E tests for banner complete (this phase)

**Independent of Phase 2**:
- Different templates (chat.html vs settings.html)
- No shared components or dependencies

---

## Session Summary Template

```markdown
### Session [Date/Time]

**Completed**:
- [ ] Steps completed this session
- [ ] Tests written and passing
- [ ] Manual testing progress

**Blockers**: None / [Description]

**Next Session**: Continue from step [X]
```

---

*Last Updated: 2025-11-15*
*Status: Ready to Start after Phase 1 (can run parallel with Phase 2)*
