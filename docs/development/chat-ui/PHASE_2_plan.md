# Phase 2: Settings Hub Page

**Phase**: 2 of 4
**Branch**: `feat/chat-ui-phase-2` (from `feat/chat-ui`)
**Status**: 📋 READY
**Estimated Time**: 1-2 hours
**Dependencies**: Phase 1 (routes must exist)
**Parallelizable**: Yes (can work concurrently with Phase 3)

---

## Goal

Create a clean, extensible settings hub page that provides access to Garmin account management and profile settings. This page replaces the old dashboard as the central location for account configuration.

**Key Deliverables**:
- New `settings.html` template with card-based layout
- Two cards: Garmin Account and Profile Settings
- Garmin card shows connection status
- Mobile responsive design
- Accessibility compliant (WCAG AA)

---

## Prerequisites

**Previous Phases**:
- Phase 1: `/settings` route exists and passes user context ✅

**Required Spec Context**:
- Lines 256-329: Settings Hub Page component specification
- Lines 359-362: Templates to Create
- Lines 491-535: Mobile Responsiveness
- Lines 537-556: Accessibility Considerations

**Current Implementation**:
- `/settings` route exists (Phase 1)
- Route passes `user` context with `garmin_linked` status
- `base.html` template available for extending

---

## Implementation Steps

### Setup

- [ ] ⏳ NEXT: Create branch `feat/chat-ui-phase-2` from `feat/chat-ui`
  ```bash
  git checkout feat/chat-ui
  git pull
  git checkout -b feat/chat-ui-phase-2
  ```

- [ ] Verify Phase 1 merged to `feat/chat-ui`
  ```bash
  git log feat/chat-ui --oneline | head -5
  ```

---

### Step 1: Settings Template Structure

**File**: `backend/app/templates/settings.html` (new file)

#### Integration Tests

- [ ] Write test: `test_settings_page_renders_with_user_context()`
  - Location: `backend/tests/integration/test_chat_ui_templates.py` (new file)
  - Test: Settings page renders for authenticated user
  - Expected: Status 200, template contains user's display name

- [ ] Write test: `test_settings_page_displays_garmin_connection_status()`
  - Test: Settings page shows "Connected" when `user.garmin_linked == True`
  - Expected: Template contains "Connected" text
  - Test: Settings page shows "Not connected" when `user.garmin_linked == False`
  - Expected: Template contains "Not connected" text

- [ ] Write test: `test_settings_page_has_navigation_links()`
  - Test: Page includes "Back to Chat" link
  - Expected: Link href="/chat"
  - Test: Page includes "Manage" link to Garmin settings
  - Expected: Link href="/garmin/link"

- [ ] Verify tests fail
  ```bash
  uv --directory backend run pytest tests/integration/test_chat_ui_templates.py -v
  ```

#### Implementation

- [ ] Create `backend/app/templates/settings.html`
  - Extend `base.html`
  - Add header with "Settings" title and "Back to Chat" link
  - Add main content area with card grid
  - Spec reference: SPECIFICATION.md lines 256-329

  ```html
  {% extends "base.html" %}

  {% block title %}Settings - Selflytics{% endblock %}

  {% block content %}
  <div class="min-h-screen bg-gray-50">
    <!-- Header -->
    <header class="bg-white shadow mb-8" data-testid="settings-header">
      <div class="max-w-7xl mx-auto px-4 py-6">
        <div class="flex items-center justify-between">
          <h1 class="text-2xl font-bold text-gray-800">Settings</h1>
          <a href="/chat/" class="text-sm text-blue-600 hover:text-blue-800" data-testid="link-back-to-chat">
            ← Back to Chat
          </a>
        </div>
      </div>
    </header>

    <!-- Main Content -->
    <main class="max-w-7xl mx-auto px-4">
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6" data-testid="settings-grid">
        <!-- Cards will be added in next steps -->
      </div>
    </main>
  </div>
  {% endblock %}
  ```

- [ ] Add test selectors (data-testid attributes)
  - `settings-header`: Header element
  - `link-back-to-chat`: Back to chat link
  - `settings-grid`: Card container

- [ ] Verify template renders
  ```bash
  uv --directory backend run pytest tests/integration/test_chat_ui_templates.py::test_settings_page_renders_with_user_context -v
  ```

- [ ] Commit: "feat(chat-ui): add settings page template structure"

---

### Step 2: Garmin Account Card

**File**: `backend/app/templates/settings.html`

#### Unit Tests

- [ ] Write test: `test_garmin_card_shows_connected_status()`
  - Location: `backend/tests/integration/test_chat_ui_templates.py`
  - Test: Card displays "Connected" when `user.garmin_linked == True`
  - Expected: Green checkmark icon and "Connected" text visible

- [ ] Write test: `test_garmin_card_shows_not_connected_status()`
  - Test: Card displays "Not connected" when `user.garmin_linked == False`
  - Expected: "Not connected" text visible, no green checkmark

- [ ] Write test: `test_garmin_card_has_manage_link()`
  - Test: Card includes "Manage →" link to `/garmin/link`
  - Expected: Link href="/garmin/link"

- [ ] Verify tests fail
  ```bash
  uv --directory backend run pytest tests/integration/test_chat_ui_templates.py -k garmin_card -v
  ```

#### Implementation

- [ ] Add Garmin Account card to settings grid
  - Add inside `settings-grid` div
  - Conditional rendering for connection status
  - Link to `/garmin/link` for management
  - Spec reference: SPECIFICATION.md lines 281-303

  ```html
  <!-- Garmin Account Card -->
  <div class="bg-white rounded-lg shadow p-6 hover:shadow-lg transition" data-testid="card-garmin">
    <div class="flex items-start">
      <svg class="h-10 w-10 text-blue-500 mr-4" fill="currentColor" viewBox="0 0 20 20" aria-hidden="true">
        <!-- Link/chain icon -->
        <path fill-rule="evenodd" d="M12.586 4.586a2 2 0 112.828 2.828l-3 3a2 2 0 01-2.828 0 1 1 0 00-1.414 1.414 4 4 0 005.656 0l3-3a4 4 0 00-5.656-5.656l-1.5 1.5a1 1 0 101.414 1.414l1.5-1.5zm-5 5a2 2 0 012.828 0 1 1 0 101.414-1.414 4 4 0 00-5.656 0l-3 3a4 4 0 105.656 5.656l1.5-1.5a1 1 0 10-1.414-1.414l-1.5 1.5a2 2 0 11-2.828-2.828l3-3z" clip-rule="evenodd"/>
      </svg>
      <div class="flex-1">
        <h2 class="text-lg font-semibold text-gray-800 mb-2">
          Garmin Account
        </h2>
        <p class="text-sm text-gray-600 mb-4">
          Manage your Garmin connection and sync activity data
        </p>
        {% if user.garmin_linked %}
        <p class="text-xs text-green-600 mb-3" data-testid="garmin-status-connected">
          <svg class="inline h-4 w-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
          </svg>
          Connected
        </p>
        {% else %}
        <p class="text-xs text-gray-500 mb-3" data-testid="garmin-status-not-connected">Not connected</p>
        {% endif %}
        <a href="/garmin/link"
           class="inline-block bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 transition text-sm"
           data-testid="link-manage-garmin"
           aria-label="Manage Garmin account connection">
          Manage →
        </a>
      </div>
    </div>
  </div>
  ```

- [ ] Add test selectors
  - `card-garmin`: Card container
  - `garmin-status-connected`: Connected status indicator
  - `garmin-status-not-connected`: Not connected status
  - `link-manage-garmin`: Manage link

- [ ] Verify tests pass
  ```bash
  uv --directory backend run pytest tests/integration/test_chat_ui_templates.py -k garmin_card -v
  ```

- [ ] Commit: "feat(chat-ui): add Garmin account card to settings"

---

### Step 3: Profile Settings Card

**File**: `backend/app/templates/settings.html`

#### Integration Tests

- [ ] Write test: `test_profile_card_displays_user_email()`
  - Location: `backend/tests/integration/test_chat_ui_templates.py`
  - Test: Card displays user's email address
  - Expected: Template contains `user.email`

- [ ] Write test: `test_profile_card_has_edit_link()`
  - Test: Card includes "Edit →" link to `/profile/edit`
  - Expected: Link href="/profile/edit" (placeholder for future)

- [ ] Verify tests fail
  ```bash
  uv --directory backend run pytest tests/integration/test_chat_ui_templates.py -k profile_card -v
  ```

#### Implementation

- [ ] Add Profile Settings card to settings grid
  - Add after Garmin card
  - Display user email
  - Link to `/profile/edit` (future implementation)
  - Spec reference: SPECIFICATION.md lines 305-323

  ```html
  <!-- Profile Settings Card -->
  <div class="bg-white rounded-lg shadow p-6 hover:shadow-lg transition" data-testid="card-profile">
    <div class="flex items-start">
      <svg class="h-10 w-10 text-purple-500 mr-4" fill="currentColor" viewBox="0 0 20 20" aria-hidden="true">
        <!-- User icon -->
        <path fill-rule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clip-rule="evenodd"/>
      </svg>
      <div class="flex-1">
        <h2 class="text-lg font-semibold text-gray-800 mb-2">
          Profile Settings
        </h2>
        <p class="text-sm text-gray-600 mb-4">
          Update your display name, email, and password
        </p>
        <p class="text-xs text-gray-500 mb-3" data-testid="profile-email">{{ user.email }}</p>
        <a href="/profile/edit"
           class="inline-block bg-purple-600 text-white px-4 py-2 rounded hover:bg-purple-700 transition text-sm"
           data-testid="link-edit-profile"
           aria-label="Edit profile settings">
          Edit →
        </a>
      </div>
    </div>
  </div>
  ```

- [ ] Add test selectors
  - `card-profile`: Card container
  - `profile-email`: Email display
  - `link-edit-profile`: Edit link

- [ ] Verify tests pass
  ```bash
  uv --directory backend run pytest tests/integration/test_chat_ui_templates.py -k profile_card -v
  ```

- [ ] Commit: "feat(chat-ui): add profile settings card to settings"

---

### Step 4: Mobile Responsive Design

**File**: `backend/app/templates/settings.html`

#### Manual Testing

- [ ] Test mobile layout (viewport < 768px)
  - Cards stack vertically (1 column)
  - Full width cards with adequate spacing
  - Touch targets ≥ 44x44px
  - Spec reference: SPECIFICATION.md lines 530-534

- [ ] Test tablet layout (768px ≤ viewport < 1024px)
  - Cards display in 2 columns
  - Proper spacing maintained

- [ ] Test desktop layout (viewport ≥ 1024px)
  - Cards display in 2 columns
  - Max width container centers content

#### Implementation

- [ ] Verify responsive grid classes
  - Current: `grid-cols-1 md:grid-cols-2`
  - Mobile: 1 column (default)
  - Tablet+: 2 columns (md breakpoint)

- [ ] Verify button touch targets
  - Buttons: `px-4 py-2` = minimum 44px height
  - Links: Adequate clickable area

- [ ] Test in browser at various widths
  ```bash
  ./scripts/dev-server.sh
  # Open http://localhost:8000/settings in browser
  # Use DevTools responsive mode to test breakpoints
  ```

- [ ] Commit: "feat(chat-ui): verify mobile responsive settings layout"

---

### Step 5: Accessibility Enhancements

**File**: `backend/app/templates/settings.html`

#### Accessibility Tests

- [ ] Verify heading hierarchy
  - `<h1>` for page title (Settings)
  - `<h2>` for card titles
  - No skipped levels

- [ ] Verify ARIA labels
  - Links have descriptive `aria-label` attributes
  - Icons have `aria-hidden="true"`

- [ ] Verify keyboard navigation
  - Tab order logical (header → cards → links)
  - All interactive elements keyboard accessible
  - Focus states visible

- [ ] Verify color contrast
  - Text meets WCAG AA (4.5:1 minimum)
  - Use browser DevTools accessibility checker

- [ ] Spec reference: SPECIFICATION.md lines 546-556

#### Implementation

- [ ] Add/verify ARIA labels on all links
  - "Back to Chat" link
  - "Manage" Garmin link: `aria-label="Manage Garmin account connection"`
  - "Edit" Profile link: `aria-label="Edit profile settings"`

- [ ] Add `aria-hidden="true"` to decorative icons
  - Already included in card icon SVGs

- [ ] Verify focus states with keyboard navigation
  ```bash
  # In browser, use Tab key to navigate
  # Verify visible focus rings on all interactive elements
  ```

- [ ] Run accessibility audit
  ```bash
  # Use browser DevTools Lighthouse accessibility audit
  # Target: 100% accessibility score
  ```

- [ ] Commit: "feat(chat-ui): add accessibility enhancements to settings"

---

### Final Validation

#### Test Verification

- [ ] Run full integration test suite
  ```bash
  uv --directory backend run pytest tests/integration -v
  ```

- [ ] Run template-specific tests
  ```bash
  uv --directory backend run pytest tests/integration/test_chat_ui_templates.py -v
  ```

- [ ] Verify 80%+ coverage maintained
  ```bash
  uv --directory backend run pytest tests/ --cov=app --cov-report=term-missing
  ```

#### Manual Verification

- [ ] Complete manual testing checklist:
  - [ ] Settings page loads at `/settings`
  - [ ] "Back to Chat" link navigates to `/chat/`
  - [ ] Garmin card shows correct connection status
  - [ ] "Manage" link navigates to `/garmin/link`
  - [ ] Profile card displays user email
  - [ ] Mobile layout stacks cards vertically
  - [ ] Tablet/desktop layout shows 2 columns
  - [ ] All links keyboard accessible
  - [ ] Focus states visible

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
  git push -u origin feat/chat-ui-phase-2
  ```

- [ ] Create PR targeting `feat/chat-ui` (NOT main)
  ```bash
  gh pr create --base feat/chat-ui --title "Phase 2: Settings Hub Page" --body "
  ## Summary
  Creates settings hub page with card-based layout:
  - New settings.html template
  - Garmin account card (shows connection status)
  - Profile settings card (displays email)
  - Mobile responsive design
  - Accessibility compliant (WCAG AA)

  ## Tests
  - Integration tests for template rendering
  - Manual testing checklist completed
  - 80%+ coverage maintained

  ## Spec Reference
  SPECIFICATION.md lines 256-329, 491-556
  "
  ```

- [ ] Update this plan: Mark all steps ✅ DONE
- [ ] Update ROADMAP.md: Phase 2 status → ✅ DONE

---

## Testing Requirements

### Integration Tests

**New Test File**: `backend/tests/integration/test_chat_ui_templates.py`

**Test Coverage**:
- Settings page renders with user context
- Garmin connection status displayed correctly (connected/not connected)
- Profile card displays user email
- Navigation links present and correct
- Template inherits from base.html properly

**Test Patterns**:
```python
from fastapi.testclient import TestClient

def test_settings_page_renders_with_user_context(client: TestClient, test_user_token):
    """Settings page should render with authenticated user context."""
    response = client.get(
        "/settings",
        cookies={"access_token": f"Bearer {test_user_token}"}
    )
    assert response.status_code == 200
    assert "Settings" in response.text
    assert "Back to Chat" in response.text

def test_garmin_card_shows_connected_status(client: TestClient, test_user_linked_garmin):
    """Garmin card should show Connected status when linked."""
    # Mock user with garmin_linked=True
    response = client.get("/settings", cookies={...})
    assert "Connected" in response.text
    assert 'data-testid="garmin-status-connected"' in response.text
```

### Manual Testing Checklist

- [ ] Settings page accessible at `/settings`
- [ ] Page requires authentication (redirects to login if not authenticated)
- [ ] Garmin card displays "Connected" when linked
- [ ] Garmin card displays "Not connected" when unlinked
- [ ] "Manage" link navigates to `/garmin/link`
- [ ] Profile card displays user's email
- [ ] "Edit" link navigates to `/profile/edit` (placeholder page)
- [ ] "Back to Chat" link returns to `/chat/`
- [ ] Mobile: Cards stack vertically (<768px)
- [ ] Desktop: Cards display in 2 columns (≥768px)
- [ ] All links keyboard accessible (Tab navigation)
- [ ] Focus states visible on all interactive elements
- [ ] Color contrast meets WCAG AA standards

### Coverage Goal

- **Target**: 100% coverage on template rendering logic
- **Minimum**: 80% overall coverage maintained

---

## Success Criteria

### Technical Validation

- [ ] `/settings` route renders `settings.html` template
- [ ] Template displays two cards: Garmin Account and Profile Settings
- [ ] Garmin card shows connection status based on `user.garmin_linked`
- [ ] Profile card displays `user.email`
- [ ] All links navigate to correct destinations

### Design Validation

- [ ] Mobile responsive (cards stack on small screens)
- [ ] Tablet/desktop layout (2 columns)
- [ ] Hover states on cards (shadow transition)
- [ ] Consistent with existing UI (matches chat/dashboard styling)

### Accessibility Validation

- [ ] Heading hierarchy correct (h1 → h2)
- [ ] ARIA labels on all links
- [ ] Keyboard navigation works
- [ ] Focus states visible
- [ ] Color contrast meets WCAG AA

### Test Validation

- [ ] All integration tests passing
- [ ] Template rendering tested with/without Garmin linked
- [ ] Navigation links verified
- [ ] 80%+ coverage maintained

---

## Notes

### Design Decisions

**Why card-based layout?**
- Extensible for future settings sections
- Visual hierarchy clear (each setting category gets a card)
- Matches modern UI patterns
- Spec explicitly requires card/tile layout (line 256)

**Why profile edit as placeholder?**
- Out of scope for this redesign (Phase 3 in spec, line 659-673)
- UI prepares for future implementation
- Clicking link shows friendly "coming soon" message

**Color scheme**:
- Garmin card: Blue theme (matches link/connection concept)
- Profile card: Purple theme (distinct from Garmin)
- Maintains consistency with Tailwind color palette

### Spec References

- **Settings hub layout**: Lines 256-329
- **Mobile responsiveness**: Lines 491-535
- **Accessibility requirements**: Lines 537-556
- **Templates to create**: Lines 359-362

### Common Patterns

**Card structure** (from spec):
```html
<div class="bg-white rounded-lg shadow p-6 hover:shadow-lg transition">
  <div class="flex items-start">
    <svg class="h-10 w-10 text-[color] mr-4">...</svg>
    <div class="flex-1">
      <h2>Title</h2>
      <p>Description</p>
      <p>Status/Info</p>
      <a href="...">Action →</a>
    </div>
  </div>
</div>
```

**Responsive grid**:
```html
<div class="grid grid-cols-1 md:grid-cols-2 gap-6">
  <!-- Cards -->
</div>
```

---

## Dependencies for Next Phase

**Phase 3 (Chat Banner) is independent** - can work in parallel:
- No shared templates (Phase 3 modifies `chat.html`)
- No route dependencies beyond Phase 1

**Phase 4 (Cleanup) requires**:
- [ ] Settings page exists and functional (this phase)
- [ ] Navigation links verified (this phase)

---

## Session Summary Template

```markdown
### Session [Date/Time]

**Completed**:
- [ ] Steps completed this session
- [ ] Tests written and passing
- [ ] Manual testing checklist progress

**Blockers**: None / [Description]

**Next Session**: Continue from step [X]
```

---

*Last Updated: 2025-11-15*
*Status: Ready to Start after Phase 1*
