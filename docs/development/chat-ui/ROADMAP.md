# Chat-Centric UI Redesign - Implementation Roadmap

**Project**: Selflytics Chat-First Navigation Redesign
**Started**: 2025-11-15
**Status**: Ready for Implementation
**Based on**: `/Users/bryn/repos/selflytics-ui/docs/development/chat-ui/SPECIFICATION.md`
**Feature Branch**: `feat/chat-ui`
**GitHub Repo**: https://github.com/anbaricideas/selflytics

---

## Executive Summary

This roadmap implements the chat-centric UI redesign, transitioning from a dashboard-first to chat-first navigation model. The redesign eliminates friction by redirecting authenticated users directly to the chat interface, repurposes the dashboard as a settings hub, and adds a dismissible Garmin connection banner.

**Core Changes**:
- Authenticated users redirect to `/chat` instead of `/dashboard`
- Dashboard repurposed as `/settings` hub page
- Dismissible Garmin banner in chat interface
- Settings icon in chat header for easy access
- Removed placeholder feature cards (Recent Activities, Goals, Visualizations)

**Key Benefits**:
- Reduces navigation steps to reach primary feature (chat)
- Simplifies UI by removing unimplemented placeholders
- Improves Garmin linking discoverability without being intrusive
- Creates clear settings hub for future account management features

---

## Implementation Strategy

### Core Principles

1. **Quick Iterations**: Optimize for 1-2 hour work sessions
2. **TDD Workflow**: Write tests first, review with quality gates, then implement
3. **Parallel Execution**: Phases 2 and 3 can be worked on concurrently
4. **Preserve Functionality**: All existing features remain unchanged
5. **Standard E2E Coverage**: Test critical navigation paths only

### Development Approach

**Phase Progression**:
```
Phase 1: Core Backend Routes (1-2h) - SEQUENTIAL
  ↓
Phase 2: Settings Hub Page (1-2h) ┐
                                   ├─ PARALLEL
Phase 3: Chat Banner & Dismissal  ┘
  ↓
Phase 4: Navigation & Cleanup (1-2h) - SEQUENTIAL
```

**Parallelization Strategy**:
- **Phase 2 and Phase 3 are independent** - different templates, no shared dependencies
- Can be implemented by different developers or in separate sessions
- Both depend on Phase 1 (routes) but not on each other

### Git Workflow

**IMPORTANT: Sub-branch strategy for feature branch**

```
feat/chat-ui (feature branch - current branch)
  ← feat/chat-ui-phase-1 (PR #1 → merges to feat/chat-ui)
  ← feat/chat-ui-phase-2 (PR #2 → merges to feat/chat-ui)
  ← feat/chat-ui-phase-3 (PR #3 → merges to feat/chat-ui)
  ← feat/chat-ui-phase-4 (PR #4 → merges to feat/chat-ui)

main (final merge after all phases complete)
  ← feat/chat-ui (PR after phases 1-4 complete)
```

**Branch Protection**:
- All phase PRs merge to `feat/chat-ui` (NOT to main)
- Each phase PR requires tests passing
- Final PR from `feat/chat-ui` to `main` requires full CI validation

### Session Startup Command

When ready to implement each phase:

```
I'm working on the chat-ui redesign. Continue with the next incomplete phase from @docs/development/chat-ui/ROADMAP.md

The roadmap points to phase planning documents. Use those as the single source of truth.

Guidelines:
1. Follow TDD: write tests first, verify fail, implement, verify pass
2. Commit after each major step
3. Track progress in phase plan checkboxes
4. Ask questions only if blocked or contradictory info found

Start from: wherever marked as ⏳ NEXT
```

---

## Phase Overview

| Phase | Description | Status | Branch | PR | Parallelizable |
|-------|-------------|--------|--------|-----|----------------|
| [1](./PHASE_1_plan.md) | Core Backend Routes | ✅ COMPLETE | `feat/chat-ui-phase-1` | #11 | No (foundation) |
| [2](./PHASE_2_plan.md) | Settings Hub Page | ⏳ NEXT | `feat/chat-ui-phase-2` | - | Yes (with Phase 3) |
| [3](./PHASE_3_plan.md) | Chat Banner & Dismissal | 📋 READY | `feat/chat-ui-phase-3` | - | Yes (with Phase 2) |
| [4](./PHASE_4_plan.md) | Navigation & Cleanup | 📋 PLANNED | `feat/chat-ui-phase-4` | - | No (needs 1-3) |

**Current Phase**: Phase 2 (Settings Hub Page)

**Parallelization Notes**:
- Phase 1 must complete first (establishes routes)
- Phases 2 and 3 can run in parallel (independent features)
- Phase 4 requires Phases 1-3 complete (cleanup and integration)

---

## Dependencies

### Required Tools (Already Installed)
- uv (package manager)
- Python 3.12+
- Playwright (for E2E tests)

### No New Dependencies Required
This is a UI redesign - all changes use existing packages.

### Environment Variables (Already Configured)
No new environment variables needed.

---

## Testing Strategy

### Test Pyramid

```
        ┌───────────┐
        │    E2E    │  Standard - Critical navigation paths
        │   Tests   │
        └───────────┘
      ┌───────────────┐
      │  Integration  │  Route tests, template rendering
      │     Tests     │
      └───────────────┘
    ┌───────────────────┐
    │   Unit Tests      │  Banner logic, localStorage helpers
    │                   │
    └───────────────────┘
```

### TDD Workflow (Every Phase)

1. **Write Test First**: Define expected behavior with test cases
2. **Verify Failure**: Run tests, confirm they fail (no implementation yet)
3. **Implement**: Write minimal code to pass tests
4. **Verify Success**: Run tests, confirm they pass
5. **Commit**: Save progress with clear commit message

### Test Organization

```
backend/tests/
├── unit/               # localStorage helpers, utility functions
├── integration/        # Route redirects, template rendering
│   └── test_chat_ui_routes.py  # New tests for route changes
└── e2e_playwright/     # Critical user navigation flows
    └── test_chat_ui_navigation.py  # New E2E tests
```

### Coverage Requirements

- **Minimum**: 80% coverage on all new code
- **Critical Paths**: E2E tests for main navigation changes
- **Standard E2E**: Test primary user journeys only (not exhaustive)

### E2E Testing Approach

**Critical navigation paths to test**:
- User logs in → redirected to `/chat` (not `/dashboard`)
- User dismisses banner → stays hidden in session
- User logs out and back in → banner reappears
- User clicks settings icon → navigates to `/settings`
- Old `/dashboard` URL → redirects to `/settings`

**Local E2E Testing**:
```bash
# Terminal 1: Start local server with emulator
./scripts/local-e2e-server.sh

# Terminal 2: Run E2E tests
uv --directory backend run pytest tests/e2e_playwright/test_chat_ui_navigation.py -v --headed
```

---

## Quality Gates

### Per-Phase Quality Checks

Before marking a phase complete:

1. **Code Quality**:
   - [ ] `uv run ruff check .` passes with no errors
   - [ ] `uv run ruff format --check .` passes
   - [ ] No f-strings in logger calls (pre-commit enforced)

2. **Testing**:
   - [ ] All new tests passing
   - [ ] 80%+ coverage on new code
   - [ ] E2E tests pass locally (critical paths only)

3. **Documentation**:
   - [ ] Phase plan updated with completion status
   - [ ] All implementation steps marked ✅ DONE
   - [ ] Commit messages follow conventional commits format

4. **Git Workflow**:
   - [ ] Branch created from `feat/chat-ui` (not main)
   - [ ] PR targets `feat/chat-ui` (not main)
   - [ ] All CI checks passing

---

## Common Commands

### Development

```bash
# Run local development server
./scripts/dev-server.sh

# Run all CI checks locally
uv run ruff check .
uv run ruff format --check .
uv --directory backend run pytest tests/ -v --cov=app

# Format code
uv run ruff format .
uv run ruff check --fix .

# Run tests by category
uv --directory backend run pytest tests/unit -v
uv --directory backend run pytest tests/integration -v
uv --directory backend run pytest tests/e2e_playwright -v
```

### Git Workflow (Sub-branch Strategy)

```bash
# IMPORTANT: Start from feat/chat-ui branch
git checkout feat/chat-ui

# Create phase sub-branch
git checkout -b feat/chat-ui-phase-1

# Stage and commit changes
git add .
git commit -m "feat(chat-ui): redirect root to /chat instead of /dashboard"

# Push to remote
git push -u origin feat/chat-ui-phase-1

# Create PR targeting feat/chat-ui (NOT main)
gh pr create --base feat/chat-ui --title "Phase 1: Core Backend Routes"

# After PR approved and merged, delete phase branch
git checkout feat/chat-ui
git pull
git branch -d feat/chat-ui-phase-1

# Repeat for next phase
```

### Hours Estimate

```bash
# Hours spent on current branch (relative to feat/chat-ui)
git log --oneline feat/chat-ui..HEAD --format="%ad" --date=format:"%Y-%m-%d %H:00" | uniq | wc -l
```

---

## Success Criteria

### Phase 1 Success Criteria (Core Backend Routes)

**Technical Success**:
- [ ] Root route (`/`) redirects to `/chat` for authenticated users
- [ ] `/dashboard` redirects to `/settings` (301 permanent)
- [ ] New `/settings` route exists and requires authentication
- [ ] All route tests passing

**Deliverables**:
- [ ] Updated root route in `main.py`
- [ ] Dashboard redirect in `dashboard.py`
- [ ] New settings route in `dashboard.py`
- [ ] Integration tests for all route changes

### Phase 2 Success Criteria (Settings Hub Page)

**Technical Success**:
- [ ] Settings page displays two cards (Garmin, Profile)
- [ ] Garmin card shows connection status
- [ ] Cards link to correct pages
- [ ] Mobile responsive layout works

**Deliverables**:
- [ ] `settings.html` template created
- [ ] Settings route renders template correctly
- [ ] Template tests passing
- [ ] Mobile responsive verified

### Phase 3 Success Criteria (Chat Banner & Dismissal)

**Technical Success**:
- [ ] Banner appears for users with unlinked Garmin accounts
- [ ] Banner dismissal persists within session
- [ ] Banner reappears after logout/login
- [ ] Logout clears banner dismissed state

**Deliverables**:
- [ ] Banner component in `chat.html`
- [ ] JavaScript dismissal logic
- [ ] localStorage integration
- [ ] Unit tests for banner logic

### Phase 4 Success Criteria (Navigation & Cleanup)

**Technical Success**:
- [ ] Settings icon in chat header works
- [ ] Placeholder cards removed from dashboard
- [ ] All tests updated and passing
- [ ] E2E tests cover critical navigation paths

**Deliverables**:
- [ ] Chat header updated with settings icon
- [ ] Dashboard template cleaned up
- [ ] Test suite updated
- [ ] E2E tests for navigation flows

### Overall Success Criteria

**Functional Requirements**:
- [ ] Authenticated users redirect to `/chat` from root URL
- [ ] Garmin banner displays for users with unlinked accounts
- [ ] Banner dismissal works and persists within session
- [ ] Banner reappears on new login session if account still unlinked
- [ ] Settings icon in chat header navigates to `/settings`
- [ ] Settings hub displays Garmin and Profile cards
- [ ] Garmin card links to `/garmin/link`
- [ ] Old `/dashboard` URL redirects to `/settings`
- [ ] Logout clears banner dismissal state
- [ ] Mobile responsive behavior works correctly

**Non-Functional Requirements**:
- [ ] No performance degradation
- [ ] Accessibility standards met (keyboard navigation, ARIA labels)
- [ ] No new security vulnerabilities
- [ ] Existing chat functionality unaffected
- [ ] All existing tests pass (with updated navigation tests)

**User Experience Goals**:
- [ ] Reduced clicks to reach chat (login → chat vs. login → dashboard → chat)
- [ ] Garmin linking discoverable but non-intrusive
- [ ] Settings easily accessible from chat interface
- [ ] Clean, uncluttered UI focused on core functionality

---

## Timeline Estimate

| Phase | Duration | Effort (hours) | Cumulative |
|-------|----------|----------------|------------|
| **Phase 1** | 1-2h | 2 | 2 |
| **Phase 2** | 1-2h | 2 | 4 (parallel with 3) |
| **Phase 3** | 1-2h | 2 | 4 (parallel with 2) |
| **Phase 4** | 1-2h | 2 | 6 |
| **TOTAL** | **4-6 sessions** | **6-8 hours** | - |

**Parallelization Benefit**: Phases 2 and 3 can run concurrently, reducing calendar time from 8 hours to 6 hours.

**Assumptions**:
- Quick work sessions (1-2 hours each)
- TDD workflow followed (tests first)
- Standard E2E coverage (critical paths only)

---

## Risk Mitigation

### Technical Risks

**Risk**: Existing E2E tests break due to navigation changes
- **Mitigation**: Update tests in Phase 4 before claiming complete
- **Mitigation**: Run full test suite locally before pushing

**Risk**: Banner localStorage conflicts with other features
- **Mitigation**: Use namespaced key (`garmin-banner-dismissed`)
- **Mitigation**: Clear on logout explicitly

**Risk**: Mobile responsive issues with banner
- **Mitigation**: Test on multiple screen sizes
- **Mitigation**: Use Tailwind responsive utilities

### Process Risks

**Risk**: Forgetting to merge to `feat/chat-ui` instead of `main`
- **Mitigation**: Document sub-branch strategy clearly in each phase plan
- **Mitigation**: Use `--base feat/chat-ui` in PR creation command

**Risk**: Phases 2 and 3 create merge conflicts
- **Mitigation**: They modify different files (settings.html vs chat.html)
- **Mitigation**: Coordinate if working with multiple developers

---

## History

| Date | Event | Notes |
|------|-------|-------|
| 2025-11-15 | Roadmap created | 4 phases, 6-8 hours estimated, parallel execution for phases 2-3 |
| 2025-11-15 | Specification finalized | Based on SPECIFICATION.md v1.0 |
| 2025-11-15 | Phase 1 completed | Core Backend Routes - route redirects and settings endpoint (PR #11 merged) |

---

## References

**Project Documentation**:
- [Specification](./SPECIFICATION.md) - Complete UI redesign specification
- [CLAUDE.md](../../../.claude/CLAUDE.md) - Development workflow and conventions
- [Main Roadmap](../../project-setup/ROADMAP.md) - Overall project roadmap

**Related Features**:
- Current chat implementation: `backend/app/templates/chat.html`
- Current dashboard: `backend/app/templates/dashboard.html`
- Authentication routes: `backend/app/routes/auth.py`
- Dashboard routes: `backend/app/routes/dashboard.py`

---

*Last Updated: 2025-11-15*
*Status: In Progress - Phase 2 Next*
