# Outstanding Tasks

## E2E Test Investigation

**Status**: Partially Complete
**Priority**: Medium

### Background
PR #19 feedback has been fully addressed. During testing, we discovered and fixed pre-existing e2e test failures caused by the `/dashboard` → `/settings` redirect in earlier chat-ui work.

### Current Status
- ✅ Fixed 8 instances of hardcoded `/dashboard` references in e2e tests
- ✅ 17+ e2e tests now passing (was 11 before fixes)
- ⚠️ Some e2e tests still timing out (needs investigation)
- ❌ 2 tests still failing (unrelated to PR #19 changes)

### Outstanding Work
1. **Investigate timing-out e2e tests**
   - Some tests hang indefinitely during execution
   - May be related to async/await patterns or Playwright configuration
   - Need to isolate which specific tests are affected

2. **Fix remaining 2 failed tests**
   - `test_banner_link_navigates_to_garmin_oauth` - FAILED
   - `test_user_login_redirects_to_chat` - FAILED
   - Investigate root cause and implement fixes

3. **Verify all e2e tests pass**
   - Run full suite with `BASE_URL=http://localhost:8042`
   - Ensure 100% pass rate before considering complete

### Files Modified (For Reference)
**PR #19 Feedback Changes**:
- `backend/app/templates/settings.html`
- `backend/app/templates/chat.html`
- `backend/app/templates/login.html`
- `docs/development/chat-ui/ROADMAP.md`
- `docs/development/chat-ui/SPECIFICATION.md`
- `docs/development/chat-ui/PHASE_3_plan.md`
- `tests/integration/test_chat_ui_templates.py`

**Dashboard→Settings E2E Test Fixes**:
- `tests/e2e_playwright/conftest.py`
- `tests/e2e_playwright/test_alpine_state.py`
- `tests/e2e_playwright/test_csrf_protection.py`
- `tests/e2e_playwright/test_garmin_linking_journey.py`
- `tests/e2e_playwright/test_user_journeys.py`

### Next Session
When resuming this work:
1. Start the e2e server: `./scripts/local-e2e-server.sh`
2. Run tests: `BASE_URL=http://localhost:8042 uv --directory backend run pytest tests/e2e_playwright -v`
3. Focus on the timing-out tests and 2 failed tests
4. Once all pass, mark this task complete
