# Chat-Centric UI Redesign Specification

**Version:** 1.0
**Date:** 2025-11-15
**Status:** Draft

## Overview

### Current State

The Selflytics application currently uses a **dashboard-first** navigation model:

1. Users log in → redirected to `/dashboard`
2. Dashboard displays:
   - Garmin connection status banner
   - Feature cards grid (Chat Analysis, Recent Activities, Goals & Tracking, Visualizations)
   - Users must click "Chat Analysis" card to access `/chat`
3. Garmin linking managed via separate `/garmin/link` page
4. Three placeholder feature cards (not yet implemented)

### Desired State

The redesign will implement a **chat-first** navigation model:

1. Users log in → redirected directly to `/chat`
2. Chat interface displays:
   - Dismissible Garmin banner (if account not linked)
   - Conversation sidebar + message interface (existing functionality)
   - Settings icon in header for accessing account/Garmin management
3. Dashboard repurposed as `/settings` hub page
4. Placeholder features removed entirely

### Goals and Objectives

**Primary Goals:**
- **Reduce friction**: Eliminate unnecessary navigation step between login and main feature
- **Simplify UI**: Remove placeholder features and focus on core chat functionality
- **Maintain functionality**: Preserve all existing features (Garmin linking, settings, logout)

**Secondary Goals:**
- Improve user onboarding by surfacing Garmin linking in context
- Create clear settings hub for future account management features
- Maintain mobile responsiveness and accessibility

---

## Design Decisions Summary

| Aspect | Decision | Rationale |
|--------|----------|-----------|
| **Post-login destination** | Directly to `/chat` | Chat is the primary feature; skip intermediate dashboard |
| **Dashboard page** | Repurposed as `/settings` hub | Keep for account/Garmin management; accessible from chat header |
| **Garmin banner** | Dismissible banner in chat UI | User can close to reduce clutter; reappears next session if unlinked |
| **Banner dismissal logic** | Once per session (localStorage) | Gentle reminder without being intrusive |
| **Settings navigation** | Icon menu (gear icon) in header | Clean, standard UI pattern; minimal header clutter |
| **Settings page layout** | Card/tile hub with links | Organized, extensible for future settings sections |
| **Root route (`/`)** | Redirect to `/chat` | Authenticated users go straight to primary interface |
| **Conversation sidebar** | Keep as-is | No changes to existing working functionality |
| **Placeholder features** | Remove entirely | Not in current scope; reduce UI clutter |

---

## User Journeys

### 1. New User - First Login (Garmin Not Linked)

```
1. User completes registration/login at /login
2. Redirected to /chat
3. Garmin banner visible at top:
   ┌─────────────────────────────────────────────────────────┐
   │ 🔗 Connect your Garmin account to analyze activity data │
   │ [Link Now]  [×]                                         │
   └─────────────────────────────────────────────────────────┘
4. User has two options:
   a. Click "Link Now" → navigates to /garmin/link page
   b. Click [×] to dismiss → banner disappears for session
5. User can access chat normally, with or without Garmin linked
```

### 2. Returning User - Subsequent Sessions

**Scenario A: Garmin Still Unlinked, Banner Previously Dismissed**
```
1. User logs in
2. Redirected to /chat
3. Banner reappears (dismissed state cleared on new session)
4. User can dismiss again or proceed to link
```

**Scenario B: Garmin Already Linked**
```
1. User logs in
2. Redirected to /chat
3. No banner displayed (Garmin account linked)
4. Full chat functionality available
```

### 3. Settings Management Flow

```
1. From chat interface, user clicks settings icon (⚙️) in header
2. Navigates to /settings page
3. Settings page displays two cards:
   ┌──────────────────────┐  ┌──────────────────────┐
   │ 🔗 Garmin Account    │  │ 👤 Profile Settings  │
   │ Manage connection,   │  │ Display name, email, │
   │ sync data            │  │ password             │
   │ [Manage →]           │  │ [Edit →]             │
   └──────────────────────┘  └──────────────────────┘
4. Clicking card navigates to relevant page:
   - Garmin Account → /garmin/link (existing page)
   - Profile Settings → /profile/edit (new page, future implementation)
5. Back navigation returns to /settings or /chat
```

### 4. Garmin Linking from Banner

```
1. User clicks "Link Now" in banner
2. Navigates to /garmin/link
3. User enters Garmin credentials
4. On success:
   a. Redirected back to /chat
   b. Banner no longer appears (Garmin linked)
5. On error:
   a. Error displayed on /garmin/link page
   b. User retries or navigates back to /chat
```

---

## Technical Implementation

### URL Routing Changes

| Route | Current Behavior | New Behavior | Notes |
|-------|------------------|--------------|-------|
| `/` | Redirects to `/dashboard` or `/login` | Redirects to `/chat` or `/login` | Authenticated users go to chat |
| `/dashboard` | Main landing page | Redirects to `/settings` | Preserve old links, redirect to new location |
| `/settings` | Does not exist | Settings hub page | New page with card/tile layout |
| `/chat` | Chat interface | Chat interface + Garmin banner (if unlinked) | Add banner logic |
| `/garmin/link` | Garmin linking page | Unchanged | Existing functionality preserved |
| `/login` | Login page | Unchanged | No changes |
| `/register` | Registration page | Unchanged | No changes |

### UI Components

#### 1. Garmin Banner (New Component)

**Location:** Top of `/chat` page (above conversation sidebar and message area)

**Visibility Conditions:**
- Only shown if `user.garmin_linked == False`
- Hidden if user dismissed in current session (checked via `localStorage`)
- Reappears on new login session (localStorage key cleared on logout)

**Content:**
```html
<div id="garmin-banner" class="bg-blue-50 border-l-4 border-blue-400 p-4">
  <div class="flex items-center justify-between">
    <div class="flex items-center">
      <svg class="h-6 w-6 text-blue-400 mr-3">...</svg>
      <p class="text-sm text-blue-700">
        Connect your Garmin account to analyze your activity data with AI
      </p>
    </div>
    <div class="flex items-center gap-4">
      <a href="/garmin/link" class="btn btn-primary btn-sm">Link Now</a>
      <button id="dismiss-banner" class="text-blue-700 hover:text-blue-900">
        <svg class="h-5 w-5">...</svg> <!-- Close icon -->
      </button>
    </div>
  </div>
</div>
```

**JavaScript Logic:**
```javascript
// On page load
document.addEventListener('DOMContentLoaded', () => {
  const banner = document.getElementById('garmin-banner');
  const dismissed = localStorage.getItem('garmin-banner-dismissed');

  if (dismissed === 'true') {
    banner.style.display = 'none';
  }

  document.getElementById('dismiss-banner')?.addEventListener('click', () => {
    banner.style.display = 'none';
    localStorage.setItem('garmin-banner-dismissed', 'true');
  });
});

// On logout (clear dismissed state)
function handleLogout() {
  localStorage.removeItem('garmin-banner-dismissed');
  // ... existing logout logic
}
```

**Mobile Responsive:**
- On mobile screens (<640px), stack elements vertically
- "Link Now" button remains prominent
- Close button stays accessible

#### 2. Chat Header with Settings Icon (Modified Component)

**Current Header:**
```html
<header class="bg-white shadow">
  <div class="flex items-center justify-between p-4">
    <h1>Selflytics Chat</h1>
    <div>
      <span>{{ user.display_name }}</span>
      <form action="/logout" method="post">
        <button>Logout</button>
      </form>
    </div>
  </div>
</header>
```

**New Header:**
```html
<header class="bg-white shadow">
  <div class="flex items-center justify-between p-4">
    <h1 class="text-xl font-bold text-gray-800">Selflytics</h1>
    <div class="flex items-center gap-4">
      <span class="text-sm text-gray-600">{{ user.display_name }}</span>
      <a href="/settings"
         class="text-gray-600 hover:text-gray-900 transition"
         title="Settings">
        <svg class="h-6 w-6">
          <!-- Gear/settings icon -->
          <path d="M12 15a3 3 0 100-6 3 3 0 000 6z"/>
          <path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06..."/>
        </svg>
      </a>
      <form action="/logout" method="post" class="inline">
        <button class="text-sm text-gray-600 hover:text-gray-900 transition">
          Logout
        </button>
      </form>
    </div>
  </div>
</header>
```

**Responsive Behavior:**
- On mobile: Consider hamburger menu or vertical stacking
- Settings icon always accessible
- User name may hide on very small screens (show only on hover/click)

#### 3. Settings Hub Page (New Component)

**Route:** `/settings`

**Template:** `backend/app/templates/settings.html`

**Layout:**
```html
{% extends "base.html" %}

{% block content %}
<div class="min-h-screen bg-gray-50">
  <header class="bg-white shadow mb-8">
    <div class="max-w-7xl mx-auto px-4 py-6">
      <div class="flex items-center justify-between">
        <h1 class="text-2xl font-bold text-gray-800">Settings</h1>
        <a href="/chat" class="text-sm text-blue-600 hover:text-blue-800">
          ← Back to Chat
        </a>
      </div>
    </div>
  </header>

  <main class="max-w-7xl mx-auto px-4">
    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">

      <!-- Garmin Account Card -->
      <div class="bg-white rounded-lg shadow p-6 hover:shadow-lg transition">
        <div class="flex items-start">
          <svg class="h-10 w-10 text-blue-500 mr-4">...</svg>
          <div class="flex-1">
            <h2 class="text-lg font-semibold text-gray-800 mb-2">
              Garmin Account
            </h2>
            <p class="text-sm text-gray-600 mb-4">
              Manage your Garmin connection and sync activity data
            </p>
            {% if user.garmin_linked %}
            <p class="text-xs text-green-600 mb-3">✓ Connected</p>
            {% else %}
            <p class="text-xs text-gray-500 mb-3">Not connected</p>
            {% endif %}
            <a href="/garmin/link"
               class="inline-block bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 transition text-sm">
              Manage →
            </a>
          </div>
        </div>
      </div>

      <!-- Profile Settings Card -->
      <div class="bg-white rounded-lg shadow p-6 hover:shadow-lg transition">
        <div class="flex items-start">
          <svg class="h-10 w-10 text-purple-500 mr-4">...</svg>
          <div class="flex-1">
            <h2 class="text-lg font-semibold text-gray-800 mb-2">
              Profile Settings
            </h2>
            <p class="text-sm text-gray-600 mb-4">
              Update your display name, email, and password
            </p>
            <p class="text-xs text-gray-500 mb-3">{{ user.email }}</p>
            <a href="/profile/edit"
               class="inline-block bg-purple-600 text-white px-4 py-2 rounded hover:bg-purple-700 transition text-sm">
              Edit →
            </a>
          </div>
        </div>
      </div>

    </div>
  </main>
</div>
{% endblock %}
```

**Future Extensibility:**
- Additional cards can be added to grid (App Preferences, Data Export, etc.)
- Maintains consistent card pattern
- Each card links to dedicated management page

#### 4. Conversation Sidebar (No Changes)

**Decision:** Keep existing sidebar implementation as-is
- Conversation list with "New Chat" button
- No additional icons or settings at bottom
- Preserve current working functionality

---

## Templates & File Changes

### Templates to Modify

1. **`backend/app/templates/chat.html`**
   - Add Garmin banner component at top (conditionally rendered)
   - Update header to include settings icon
   - Add JavaScript for banner dismissal logic

2. **`backend/app/templates/base.html`**
   - Ensure logout handler clears `localStorage` (if not already handled)

### Templates to Create

1. **`backend/app/templates/settings.html`** (new)
   - Settings hub page with card/tile layout
   - Links to Garmin and Profile management

2. **`backend/app/templates/profile_edit.html`** (future implementation)
   - Profile editing form
   - Not in initial scope, but mentioned for completeness

### Templates to Remove/Deprecate

1. **`backend/app/templates/dashboard.html`**
   - Can be removed after redirect is in place
   - Or kept temporarily with redirect logic for gradual migration

---

## Backend Route Changes

### `backend/app/main.py` (Root Route)

**Current:**
```python
@app.get("/")
async def root(request: Request):
    if is_authenticated(request):
        return RedirectResponse("/dashboard")
    return RedirectResponse("/login")
```

**New:**
```python
@app.get("/")
async def root(request: Request):
    if is_authenticated(request):
        return RedirectResponse("/chat")
    return RedirectResponse("/login")
```

### `backend/app/routes/dashboard.py` (New Settings Route)

**Add new route:**
```python
@router.get("/settings", response_class=HTMLResponse)
async def settings_page(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """Settings hub page with Garmin and profile management links."""
    return templates.TemplateResponse(
        "settings.html",
        {
            "request": request,
            "user": current_user,
        }
    )
```

**Add redirect for old dashboard URL:**
```python
@router.get("/dashboard")
async def dashboard_redirect():
    """Redirect old dashboard URL to new settings page."""
    return RedirectResponse("/settings", status_code=301)
```

### `backend/app/routes/chat.py` (Pass Garmin Status)

**Current:**
```python
@router.get("/", response_class=HTMLResponse)
async def chat_page(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    return templates.TemplateResponse(
        "chat.html",
        {"request": request, "user": current_user}
    )
```

**Modified (no changes needed):**
- Template already receives `user` object with `garmin_linked` status
- Banner will check this value in Jinja2 template

### `backend/app/routes/auth.py` (Logout - Clear Banner State)

**Current logout:**
```python
@router.post("/logout")
async def logout():
    response = RedirectResponse("/login", status_code=302)
    response.delete_cookie("access_token")
    return response
```

**Note:** localStorage is client-side only; no backend changes needed
- Banner dismissal state cleared via JavaScript on logout
- Consider adding this to existing logout button onclick handler

---

## Frontend Logic & State Management

### Banner Dismissal State

**Storage:** `localStorage` (client-side)

**Key:** `garmin-banner-dismissed`

**Values:**
- `"true"` = dismissed in current session
- `null` or absent = not dismissed

**Lifecycle:**
1. **On page load (`/chat`):**
   - Check `localStorage.getItem('garmin-banner-dismissed')`
   - If `"true"`, hide banner via CSS (`display: none`)
   - If `null`, show banner (default state)

2. **On dismiss click:**
   - Set `localStorage.setItem('garmin-banner-dismissed', 'true')`
   - Hide banner with animation (fade out or slide up)

3. **On logout:**
   - Clear `localStorage.removeItem('garmin-banner-dismissed')`
   - Ensures banner reappears on next login

### Authentication Check

**No changes needed:**
- Existing JWT authentication middleware continues to work
- All protected routes (`/chat`, `/settings`) require authentication
- Unauthenticated users redirected to `/login`

---

## Mobile Responsiveness

### Chat Interface with Banner

**Desktop (≥768px):**
```
┌─────────────────────────────────────────────────┐
│ Garmin Banner (full width)                      │
├──────────────┬──────────────────────────────────┤
│ Sidebar      │ Message Area                     │
│ (25%)        │ (75%)                            │
│              │                                  │
└──────────────┴──────────────────────────────────┘
```

**Mobile (<768px):**
```
┌──────────────────┐
│ Garmin Banner    │
│ (stacked)        │
├──────────────────┤
│ Sidebar toggle   │
├──────────────────┤
│ Message Area     │
│ (full width)     │
│                  │
└──────────────────┘
```

**Banner Mobile Adjustments:**
- Stack icon, message, and buttons vertically
- "Link Now" button spans full width
- Close button positioned top-right
- Reduce padding for compact display

**Settings Page Mobile:**
- Cards stack vertically (1 column) on mobile
- Full width cards with adequate touch targets
- Maintain visual hierarchy and spacing

---

## Accessibility Considerations

### Banner
- **Keyboard navigation:** Close button and "Link Now" must be keyboard accessible
- **ARIA labels:** Add `role="alert"` or `role="banner"` as appropriate
- **Screen readers:** Ensure message text is clear and actionable
- **Focus management:** When dismissed, focus moves to first interactive element in chat

### Settings Icon
- **Tooltip/title:** "Settings" text on hover
- **Keyboard accessible:** Tab navigation includes icon
- **ARIA label:** `aria-label="Settings"`
- **Visual indicator:** Hover state distinct from default state

### Settings Hub
- **Headings:** Proper heading hierarchy (`<h1>` for page, `<h2>` for cards)
- **Link text:** Descriptive ("Manage Garmin Account" not just "Manage")
- **Focus states:** Clear visual focus indicators on cards and buttons
- **Color contrast:** Ensure text meets WCAG AA standards (4.5:1 minimum)

---

## Security Considerations

### No New Security Risks

The redesign primarily involves UI reorganization with no new authentication or data handling:

1. **Existing security measures preserved:**
   - JWT authentication for all protected routes
   - httponly cookies prevent XSS attacks
   - Garmin credentials encrypted via KMS (unchanged)
   - PII redaction in logs (unchanged)

2. **localStorage usage:**
   - Only stores non-sensitive UI preference (`garmin-banner-dismissed`)
   - No authentication tokens or user data in localStorage
   - Safe for use with banner dismissal state

3. **Route protection:**
   - `/chat`, `/settings`, `/garmin/link` all remain protected routes
   - Authentication middleware unchanged

### Best Practices

- **CSRF tokens:** Ensure logout form includes CSRF token (if using CSRF middleware)
- **Rate limiting:** Consider rate limiting on `/garmin/link` to prevent brute force
- **Input validation:** Profile edit form (future) must validate all inputs

---

## Out of Scope

### Features Explicitly Removed

1. **Recent Activities card** (dashboard placeholder)
2. **Goals & Tracking card** (dashboard placeholder)
3. **Visualizations card** (dashboard placeholder)

**Rationale:** These features were never implemented and are not part of current roadmap. Removing reduces UI clutter and focuses on core chat functionality.

### Future Considerations (Not in This Redesign)

1. **Profile editing functionality** (`/profile/edit`)
   - Mentioned in settings hub but not implemented yet
   - Requires separate specification and implementation

2. **Advanced banner features:**
   - Periodic re-display (e.g., after 7 days)
   - Banner variants based on user journey
   - A/B testing different messaging

3. **Settings page expansions:**
   - App preferences (theme, notifications)
   - Data export/import
   - Usage statistics

4. **Conversation sidebar enhancements:**
   - Collapsible sections (Today, This Week, etc.)
   - Search conversations
   - Pin important conversations

---

## Implementation Phases

### Phase 1: Core UI Changes (Priority 1)

**Deliverables:**
1. Update root route (`/` → `/chat`)
2. Add Garmin banner to `/chat` template
3. Implement banner dismissal logic (JavaScript + localStorage)
4. Add settings icon to chat header
5. Create `/settings` hub page
6. Add `/dashboard` → `/settings` redirect

**Estimated Effort:** 4-6 hours

**Testing Requirements:**
- Banner appears for unlinked users
- Banner dismissal persists until logout
- Banner reappears after logout/login
- Settings icon navigates correctly
- Settings hub displays both cards
- Mobile responsiveness verified

### Phase 2: Cleanup & Polish (Priority 2)

**Deliverables:**
1. Remove placeholder feature cards references
2. Update navigation tests (e.g., root route tests)
3. Remove or deprecate `dashboard.html` template
4. Update documentation (README, user guides)
5. Accessibility audit and fixes

**Estimated Effort:** 2-3 hours

**Testing Requirements:**
- All existing tests pass
- Navigation flow tests updated
- Accessibility tests pass (WCAG AA)

### Phase 3: Profile Editing (Future - Priority 3)

**Deliverables:**
1. Create `/profile/edit` page and route
2. Implement profile update form (display name, email, password)
3. Add validation and error handling
4. Update settings card to link to new page

**Estimated Effort:** 6-8 hours (TBD)

**Testing Requirements:**
- Form validation tests
- Profile update integration tests
- Security tests (password change, email verification)

---

## Success Criteria

### Functional Requirements

- [x] Authenticated users redirect to `/chat` from root URL
- [x] Garmin banner displays for users with unlinked accounts
- [x] Banner dismissal works and persists until logout
- [x] Banner reappears on new login session if account still unlinked
- [x] Settings icon in chat header navigates to `/settings`
- [x] Settings hub displays Garmin and Profile cards
- [x] Garmin card links to `/garmin/link`
- [x] Old `/dashboard` URL redirects to `/settings`
- [x] Login clears banner dismissal state
- [x] Mobile responsive behavior works correctly

### Non-Functional Requirements

- [x] No performance degradation (banner adds minimal overhead)
- [x] Accessibility standards met (WCAG AA)
- [x] No new security vulnerabilities introduced
- [x] Existing chat functionality unaffected
- [x] All existing tests pass (with updated navigation tests)

### User Experience Goals

- [x] Reduced clicks to reach chat (login → chat vs. login → dashboard → chat)
- [x] Garmin linking discoverable but non-intrusive
- [x] Settings easily accessible from chat interface
- [x] Clean, uncluttered UI focused on core functionality

---

## Appendix A: Visual Mockups

### Chat Interface with Banner

```
┌────────────────────────────────────────────────────────────┐
│ 🔗 Connect your Garmin account to analyze activity data    │
│ [Link Now]  [×]                                            │
├──────────────┬─────────────────────────────────────────────┤
│              │ Selflytics        👤 John    ⚙️  [Logout]  │
│ Conversations├─────────────────────────────────────────────┤
│              │                                             │
│ [+ New Chat] │ Messages appear here...                     │
│              │                                             │
│ Yesterday:   │                                             │
│ • Morning run│                                             │
│ • Cycling    │                                             │
│              │                                             │
│ Last week:   │                                             │
│ • Sleep      │                                             │
│              │                                             │
│              ├─────────────────────────────────────────────┤
│              │ [Type a message...]              [Send]     │
└──────────────┴─────────────────────────────────────────────┘
```

### Settings Hub Page

```
┌────────────────────────────────────────────────────────────┐
│ Settings                              ← Back to Chat       │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  ┌─────────────────────┐  ┌─────────────────────┐        │
│  │ 🔗 Garmin Account   │  │ 👤 Profile Settings │        │
│  │                     │  │                     │        │
│  │ Manage connection,  │  │ Display name, email,│        │
│  │ sync data           │  │ password            │        │
│  │                     │  │                     │        │
│  │ ✓ Connected         │  │ john@example.com    │        │
│  │                     │  │                     │        │
│  │ [Manage →]          │  │ [Edit →]            │        │
│  └─────────────────────┘  └─────────────────────┘        │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

---

## Appendix B: Code Snippets

### Banner JavaScript (Standalone)

```javascript
// File: backend/app/templates/chat.html (embedded script)

document.addEventListener('DOMContentLoaded', () => {
  const banner = document.getElementById('garmin-banner');
  if (!banner) return; // Banner not present (already linked)

  // Check dismissed state
  const dismissed = localStorage.getItem('garmin-banner-dismissed');
  if (dismissed === 'true') {
    banner.style.display = 'none';
  }

  // Handle dismiss click
  const dismissBtn = document.getElementById('dismiss-banner');
  dismissBtn?.addEventListener('click', () => {
    banner.style.display = 'none';
    localStorage.setItem('garmin-banner-dismissed', 'true');
  });
});

// Clear banner state on logout
function handleLogout() {
  localStorage.removeItem('garmin-banner-dismissed');
  document.querySelector('form[action="/logout"]').submit();
}
```

### Settings Route (FastAPI)

```python
# File: backend/app/routes/dashboard.py

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from app.auth.dependencies import get_current_user
from app.models.user import User
from app.templates import templates

router = APIRouter()

@router.get("/settings", response_class=HTMLResponse)
async def settings_page(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """Settings hub page with Garmin and profile management links."""
    return templates.TemplateResponse(
        "settings.html",
        {
            "request": request,
            "user": current_user,
        }
    )

@router.get("/dashboard")
async def dashboard_redirect():
    """Redirect old dashboard URL to new settings page."""
    return RedirectResponse("/settings", status_code=301)
```

---

## Appendix C: Testing Checklist

### Manual Testing Scenarios

- [ ] **New user flow:**
  - Register → lands on `/chat`
  - Banner visible (Garmin not linked)
  - Click "Link Now" → navigates to `/garmin/link`
  - Complete linking → redirected to `/chat`
  - Banner no longer visible

- [ ] **Banner dismissal:**
  - Dismiss banner → disappears
  - Refresh page → banner stays hidden
  - Logout and login → banner reappears
  - Link Garmin → banner never appears again

- [ ] **Settings navigation:**
  - Click settings icon → navigates to `/settings`
  - Settings page shows both cards
  - Click "Manage" on Garmin card → navigates to `/garmin/link`
  - "Back to Chat" link returns to `/chat`

- [ ] **Old URLs:**
  - Visit `/dashboard` → redirects to `/settings`
  - Visit `/` while authenticated → redirects to `/chat`

- [ ] **Mobile responsiveness:**
  - Banner stacks vertically on mobile
  - Settings icon visible and clickable
  - Settings cards stack vertically
  - All touch targets ≥44x44px

### Automated Test Coverage

- [ ] **Route tests:**
  - Root route redirects to `/chat` when authenticated
  - `/dashboard` redirects to `/settings` (301 permanent)
  - `/settings` requires authentication
  - Unauthenticated users redirect to `/login`

- [ ] **Template rendering:**
  - Banner renders when `user.garmin_linked == False`
  - Banner absent when `user.garmin_linked == True`
  - Settings icon present in chat header
  - Settings page renders both cards

- [ ] **Integration tests:**
  - Full flow: login → chat → dismiss banner → logout → login → banner reappears
  - Link Garmin → banner disappears
  - Settings navigation → correct templates served

---

## Change Log

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-11-15 | Initial draft | Complete specification based on design discussion |

---

## Approval & Sign-off

**Stakeholders:**
- [ ] Product Owner: _______________ Date: _______
- [ ] Tech Lead: _______________ Date: _______
- [ ] Design Review: _______________ Date: _______

**Implementation Start Date:** TBD
**Target Completion Date:** TBD

---

*End of Specification*
