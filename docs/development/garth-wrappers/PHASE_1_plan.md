# Phase 1: Wrapper Implementation & Integration

**Branch**: `[current-branch]-phase-1`
**Status**: ⏳ NEXT
**Estimated Time**: 1.5 hours
**Actual Time**: -
**Started**: -
**Completed**: -

---

## Goal

Create the typed wrapper module around Garth library operations and integrate it into existing Garmin client code. This phase implements all wrapper functions with runtime validation, updates integration points to use wrappers, and removes all `type: ignore` comments related to Garth.

**Key Deliverables**:
- `backend/app/services/garth_wrapper.py` with all wrapper functions
- Token operation wrappers (OAuth1/OAuth2 get/set, profile access)
- Data retrieval wrappers (activities, daily summary, health snapshot)
- Updated `garmin_client.py` using wrappers (7 locations)
- Updated `garmin_service.py` using wrappers (1 location)
- All Garth-related `type: ignore` comments removed
- Comprehensive unit tests (90%+ coverage on wrapper module)
- Integration tests verifying wrappers are called

**Type Safety Impact**:
- Eliminates 8 `type: ignore` comments
- Enables mypy validation of Garth integration
- Documents expected Garth API structure via Pydantic models

---

## Prerequisites

**Required Before Starting**:
- [ ] Current branch checked out (main feature branch for Garth wrappers)
- [ ] Specification read: `/Users/bryn/repos/selflytics-garth/docs/development/garth-wrappers/SPECIFICATION.md`
- [ ] Roadmap reviewed: `/Users/bryn/repos/selflytics-garth/docs/development/garth-wrappers/ROADMAP.md`
- [ ] All existing tests passing: `uv --directory backend run pytest tests/ -v`

**Specification Context**:
- Lines 175-243: File structure and validation models
- Lines 254-353: Token operation wrappers (get/set oauth1/oauth2)
- Lines 358-497: Data retrieval wrappers (activities, daily_summary, health_snapshot, profile)
- Lines 501-578: Integration updates for garmin_client.py and garmin_service.py
- Lines 629-746: Unit test examples
- Lines 751-803: Integration test examples

---

## Deliverables

### New Files
- [ ] `backend/app/services/garth_wrapper.py` - Typed wrapper functions (~470 lines)
- [ ] `backend/tests/unit/test_garth_wrapper.py` - Wrapper unit tests (~250 lines)

### Modified Files
- [ ] `backend/app/services/garmin_client.py` - Use wrappers (7 locations: lines 79, 80, 96, 97, 156, 200, 227)
- [ ] `backend/app/services/garmin_service.py` - Use wrapper (1 location: line 198)
- [ ] `backend/tests/integration/test_garmin_client.py` - Add wrapper verification tests

---

## Implementation Steps

### Setup

- [ ] ⏳ NEXT: Create phase branch from current branch
  ```bash
  git checkout [current-branch]
  git pull origin [current-branch]  # Ensure up to date if collaborative
  git checkout -b [current-branch]-phase-1
  ```

---

### Step 1: Create Wrapper Module with Token Models

**Goal**: Create `garth_wrapper.py` with token validation models

**File**: `backend/app/services/garth_wrapper.py`

#### Unit Tests

- [ ] Write tests for token validation models
  - [ ] Test: `test_oauth1_token_valid_structure` - Valid OAuth1 token accepted
  - [ ] Test: `test_oauth1_token_extra_fields_allowed` - Extra fields don't cause errors
  - [ ] Test: `test_oauth1_token_missing_required_fails` - Missing required fields detected
  - [ ] Test: `test_oauth2_token_valid_structure` - Valid OAuth2 token accepted
  - [ ] Test: `test_profile_response_valid` - Valid profile accepted

- [ ] Verify tests fail (no implementation yet)
  ```bash
  uv --directory backend run pytest backend/tests/unit/test_garth_wrapper.py::TestTokenModels -v
  ```

#### Implementation

- [ ] Create file header with imports (spec lines 199-209)
  ```python
  """Typed wrapper functions for Garth library integration."""

  import logging
  from typing import Any

  import garth
  from pydantic import BaseModel, ValidationError
  from telemetry.logging_utils import redact_for_logging

  from app.models.garmin_data import DailyMetrics, GarminActivity, HealthSnapshot

  logger = logging.getLogger(__name__)
  ```

- [ ] Implement token validation models (spec lines 212-236)
  - [ ] `GarthOAuth1Token` - oauth_token, oauth_token_secret, extra="allow"
  - [ ] `GarthOAuth2Token` - access_token, token_type, expires_in, refresh_token, extra="allow"
  - [ ] `GarthProfileResponse` - displayName, extra="allow"

- [ ] Verify tests pass
  ```bash
  uv --directory backend run pytest backend/tests/unit/test_garth_wrapper.py::TestTokenModels -v
  ```

- [ ] Commit progress
  ```bash
  git add backend/app/services/garth_wrapper.py backend/tests/unit/test_garth_wrapper.py
  git commit -m "feat: Add Garth token validation models"
  ```

**Success Criteria**:
- [ ] File created with proper imports at top
- [ ] Three token models defined with Pydantic
- [ ] Models use `extra="allow"` for forward compatibility
- [ ] Tests validate model structure
- [ ] All imports from telemetry work correctly

**Reference**: Spec lines 196-236

---

### Step 2: Implement OAuth Token Operation Wrappers

**Goal**: Add get/set functions for OAuth1 and OAuth2 tokens

**File**: `backend/app/services/garth_wrapper.py`

#### Unit Tests

- [ ] Write tests for OAuth token operations
  - [ ] Test: `test_get_oauth1_token_valid` - Returns token when structure valid
  - [ ] Test: `test_get_oauth1_token_extra_fields` - Accepts extra fields without warning
  - [ ] Test: `test_get_oauth1_token_missing_required` - Logs warning but returns data
  - [ ] Test: `test_set_oauth1_token_valid` - Sets token when structure valid
  - [ ] Test: `test_set_oauth1_token_invalid` - Logs warning but still sets token
  - [ ] Test: `test_get_oauth2_token_valid` - Returns token when structure valid
  - [ ] Test: `test_set_oauth2_token_valid` - Sets token when structure valid
  - [ ] Test: `test_set_oauth2_token_invalid` - Logs warning but still sets token

- [ ] Verify tests fail (no implementation yet)
  ```bash
  uv --directory backend run pytest backend/tests/unit/test_garth_wrapper.py::TestTokenOperations -v
  ```

#### Implementation

- [ ] Implement `get_oauth1_token()` (spec lines 255-279)
  - [ ] Get token from `garth.client.oauth1_token`
  - [ ] Validate with `GarthOAuth1Token.model_validate()`
  - [ ] Log warning with `redact_for_logging()` if validation fails
  - [ ] Return raw token (non-blocking approach)

- [ ] Implement `set_oauth1_token(token)` (spec lines 282-302)
  - [ ] Validate token before setting (non-blocking)
  - [ ] Log warning with `redact_for_logging()` if invalid
  - [ ] Set `garth.client.oauth1_token = token`

- [ ] Implement `get_oauth2_token()` (spec lines 305-328)
  - [ ] Get token from `garth.client.oauth2_token`
  - [ ] Validate with `GarthOAuth2Token.model_validate()`
  - [ ] Log warning with `redact_for_logging()` if validation fails
  - [ ] Return raw token

- [ ] Implement `set_oauth2_token(token)` (spec lines 332-352)
  - [ ] Validate token before setting (non-blocking)
  - [ ] Log warning with `redact_for_logging()` if invalid
  - [ ] Set `garth.client.oauth2_token = token`

- [ ] Verify tests pass
  ```bash
  uv --directory backend run pytest backend/tests/unit/test_garth_wrapper.py::TestTokenOperations -v
  ```

- [ ] Verify no f-strings in logger calls
  ```bash
  grep -n 'logger.*f"' backend/app/services/garth_wrapper.py
  # Should return empty
  ```

- [ ] Commit progress
  ```bash
  git add backend/app/services/garth_wrapper.py backend/tests/unit/test_garth_wrapper.py
  git commit -m "feat: Add OAuth token get/set wrappers with validation"
  ```

**Success Criteria**:
- [ ] Four token wrapper functions implemented
- [ ] All functions have complete docstrings (Args/Returns/Raises/Note sections)
- [ ] Validation errors logged with `redact_for_logging()`
- [ ] Non-blocking approach (warnings don't raise exceptions)
- [ ] Tests verify both valid and invalid token handling
- [ ] No f-strings in logger calls

**Reference**: Spec lines 254-353

---

### Step 3: Implement Data Retrieval Wrappers

**Goal**: Add typed wrappers for activities, daily summary, health snapshot, and profile

**File**: `backend/app/services/garth_wrapper.py`

#### Unit Tests

- [ ] Write tests for data retrieval wrappers
  - [ ] Test: `test_get_activities_typed_valid` - Valid activities returned
  - [ ] Test: `test_get_activities_typed_multiple` - Multiple activities handled
  - [ ] Test: `test_get_activities_typed_missing_required` - Warns but returns data
  - [ ] Test: `test_get_activities_typed_invalid_type` - Warns on type mismatch
  - [ ] Test: `test_get_daily_summary_typed_valid` - Valid summary returned
  - [ ] Test: `test_get_daily_summary_typed_missing_fields` - Warns but returns data
  - [ ] Test: `test_get_health_snapshot_typed_valid` - Valid snapshot returned
  - [ ] Test: `test_get_health_snapshot_typed_missing_fields` - Warns but returns data
  - [ ] Test: `test_get_user_profile_typed_valid` - Valid profile returned
  - [ ] Test: `test_get_user_profile_typed_missing_display_name` - Handles optional fields

- [ ] Verify tests fail (no implementation yet)
  ```bash
  uv --directory backend run pytest backend/tests/unit/test_garth_wrapper.py::TestDataRetrieval -v
  ```

#### Implementation

- [ ] Implement `get_activities_typed(date_str)` (spec lines 358-388)
  - [ ] Call `garth.activities(date_str)`
  - [ ] Validate each activity with `GarminActivity(**activity)`
  - [ ] Log warning with `redact_for_logging()` on validation error
  - [ ] Return raw activities list

- [ ] Implement `get_daily_summary_typed(date_str)` (spec lines 391-432)
  - [ ] Call `garth.daily_summary(date_str)`
  - [ ] Validate by constructing `DailyMetrics` instance
  - [ ] Log warning with `redact_for_logging()` on validation error
  - [ ] Return raw summary dict

- [ ] Implement `get_health_snapshot_typed()` (spec lines 435-468)
  - [ ] Call `garth.health_snapshot()`
  - [ ] Validate by constructing `HealthSnapshot` instance
  - [ ] Log warning with `redact_for_logging()` on validation error
  - [ ] Return raw snapshot dict

- [ ] Implement `get_user_profile_typed()` (spec lines 471-497)
  - [ ] Get `garth.client.profile`
  - [ ] Validate with `GarthProfileResponse.model_validate()`
  - [ ] Log warning with `redact_for_logging()` on validation error
  - [ ] Return raw profile dict

- [ ] Verify tests pass
  ```bash
  uv --directory backend run pytest backend/tests/unit/test_garth_wrapper.py::TestDataRetrieval -v
  ```

- [ ] Verify coverage on wrapper module
  ```bash
  uv --directory backend run pytest backend/tests/unit/test_garth_wrapper.py -v \
    --cov=app.services.garth_wrapper --cov-report=term-missing --cov-fail-under=90
  ```

- [ ] Commit progress
  ```bash
  git add backend/app/services/garth_wrapper.py backend/tests/unit/test_garth_wrapper.py
  git commit -m "feat: Add data retrieval wrappers with validation"
  ```

**Success Criteria**:
- [ ] Four data retrieval functions implemented
- [ ] All functions have complete docstrings
- [ ] Reuse existing Pydantic models (GarminActivity, DailyMetrics, HealthSnapshot)
- [ ] All validation errors logged with `redact_for_logging()`
- [ ] Non-blocking validation (warnings only)
- [ ] 90%+ coverage on wrapper module
- [ ] No f-strings in logger calls

**Reference**: Spec lines 358-497

---

### Step 4: Update garmin_client.py Integration Points

**Goal**: Replace direct Garth calls with typed wrappers in `garmin_client.py`

**File**: `backend/app/services/garmin_client.py`

#### Unit Tests

- [ ] Existing unit tests should continue passing without modification
  ```bash
  uv --directory backend run pytest backend/tests/unit/test_garmin_client.py -v
  ```

#### Implementation

- [ ] Add wrapper imports to top of file (after line 7)
  ```python
  from app.services.garth_wrapper import (
      get_activities_typed,
      get_daily_summary_typed,
      get_health_snapshot_typed,
      get_oauth1_token,
      get_oauth2_token,
      set_oauth1_token,
      set_oauth2_token,
  )
  ```

- [ ] Update line 79: Replace `garth.client.oauth1_token = oauth1`
  ```python
  # Before
  garth.client.oauth1_token = oauth1  # type: ignore[assignment]

  # After
  set_oauth1_token(oauth1)
  ```

- [ ] Update line 80: Replace `garth.client.oauth2_token = oauth2`
  ```python
  # Before
  garth.client.oauth2_token = oauth2

  # After
  set_oauth2_token(oauth2)
  ```

- [ ] Update line 96: Replace `garth.client.oauth1_token` read
  ```python
  # Before
  oauth1_encrypted = encrypt_token(garth.client.oauth1_token)  # type: ignore[arg-type]

  # After
  oauth1_encrypted = encrypt_token(get_oauth1_token())
  ```

- [ ] Update line 97: Replace `garth.client.oauth2_token` read
  ```python
  # Before
  oauth2_encrypted = encrypt_token(garth.client.oauth2_token)  # type: ignore[arg-type]

  # After
  oauth2_encrypted = encrypt_token(get_oauth2_token())
  ```

- [ ] Update line 156: Replace `garth.activities` call
  ```python
  # Before
  day_activities = await asyncio.to_thread(garth.activities, current_date.isoformat())  # type: ignore[attr-defined]

  # After
  day_activities = await asyncio.to_thread(
      get_activities_typed,
      current_date.isoformat()
  )
  ```

- [ ] Update line 200: Replace `garth.daily_summary` call
  ```python
  # Before
  summary = await asyncio.to_thread(garth.daily_summary, target_date.isoformat())  # type: ignore[attr-defined]

  # After
  summary = await asyncio.to_thread(
      get_daily_summary_typed,
      target_date.isoformat()
  )
  ```

- [ ] Update line 227: Replace `garth.health_snapshot` call
  ```python
  # Before
  health_data = await asyncio.to_thread(garth.health_snapshot)  # type: ignore[attr-defined]

  # After
  health_data = await asyncio.to_thread(get_health_snapshot_typed)
  ```

- [ ] Verify no direct garth.client access remains
  ```bash
  grep -n "garth.client" backend/app/services/garmin_client.py
  # Should only find imports/mocks, no direct usage
  ```

- [ ] Verify all type: ignore comments removed
  ```bash
  grep -n "type: ignore" backend/app/services/garmin_client.py | grep -E "(garth|oauth|activities|daily_summary|health_snapshot)"
  # Should return empty
  ```

- [ ] Run unit tests to verify no regressions
  ```bash
  uv --directory backend run pytest backend/tests/unit/test_garmin_client.py -v
  ```

- [ ] Commit progress
  ```bash
  git add backend/app/services/garmin_client.py
  git commit -m "refactor: Update garmin_client to use typed Garth wrappers"
  ```

**Success Criteria**:
- [ ] Wrapper imports added to top of file
- [ ] All 7 locations updated to use wrappers
- [ ] No direct `garth.client` access (except in tests)
- [ ] All Garth-related `type: ignore` comments removed from garmin_client.py
- [ ] Existing unit tests still passing
- [ ] Code passes ruff linting

**Reference**: Spec lines 501-561

---

### Step 5: Update garmin_service.py Integration Point

**Goal**: Replace direct Garth profile access with typed wrapper in `garmin_service.py`

**File**: `backend/app/services/garmin_service.py`

#### Unit Tests

- [ ] Existing unit tests should continue passing
  ```bash
  uv --directory backend run pytest backend/tests/unit/test_garmin_service_user_profile.py -v
  ```

#### Implementation

- [ ] Add wrapper import to top of file (after line 7)
  ```python
  from app.services.garth_wrapper import get_user_profile_typed
  ```

- [ ] Update line 198: Replace direct profile access
  ```python
  # Before
  display_name: str = garth.client.profile.get("displayName", "User")

  # After
  profile = get_user_profile_typed()
  display_name: str = profile.get("displayName", "User")
  ```

- [ ] Verify no direct garth.client access remains
  ```bash
  grep -n "garth.client" backend/app/services/garmin_service.py
  # Should only find imports/comments, no direct usage
  ```

- [ ] Verify type: ignore comment removed
  ```bash
  grep -n "type: ignore" backend/app/services/garmin_service.py | grep -E "(garth|profile)"
  # Should return empty
  ```

- [ ] Run unit tests to verify no regressions
  ```bash
  uv --directory backend run pytest backend/tests/unit/test_garmin_service_user_profile.py -v
  ```

- [ ] Commit progress
  ```bash
  git add backend/app/services/garmin_service.py
  git commit -m "refactor: Update garmin_service to use typed profile wrapper"
  ```

**Success Criteria**:
- [ ] Wrapper import added to top of file
- [ ] Profile access updated to use `get_user_profile_typed()`
- [ ] Type: ignore comment removed from line 198
- [ ] Existing unit tests still passing
- [ ] Code passes ruff linting

**Reference**: Spec lines 565-578

---

### Step 6: Add Integration Tests for Wrapper Usage

**Goal**: Verify that client code actually uses typed wrappers (not direct Garth calls)

**File**: `backend/tests/integration/test_garmin_client.py`

#### Implementation

- [ ] Add integration test verifying activity wrapper usage (spec lines 760-783)
  ```python
  @pytest.mark.asyncio
  @patch("app.services.garth_wrapper.get_activities_typed")
  async def test_garmin_client_uses_activity_wrapper(mock_get_activities):
      """Verify GarminClient calls typed wrapper instead of raw garth."""
      # Setup mock to return valid activity data
      mock_get_activities.return_value = [
          {
              "activityId": 123,
              "activityName": "Morning Run",
              "activityType": "running",
              "startTimeLocal": "2025-11-16T06:00:00",
          }
      ]

      # ... test implementation
      # Verify wrapper was called (not raw garth.activities)
  ```

- [ ] Add integration test verifying token wrapper usage (spec lines 786-802)
  ```python
  @pytest.mark.asyncio
  @patch("app.services.garth_wrapper.set_oauth1_token")
  @patch("app.services.garth_wrapper.set_oauth2_token")
  async def test_garmin_client_uses_token_wrappers(
      mock_set_oauth2, mock_set_oauth1, mock_firestore
  ):
      """Verify GarminClient sets tokens via typed wrappers."""
      # ... test implementation
      # Verify wrappers were called
  ```

- [ ] Run integration tests
  ```bash
  uv --directory backend run pytest backend/tests/integration/test_garmin_client.py -v -k "wrapper"
  ```

- [ ] Commit progress
  ```bash
  git add backend/tests/integration/test_garmin_client.py
  git commit -m "test: Add integration tests verifying wrapper usage"
  ```

**Success Criteria**:
- [ ] Integration tests verify wrappers are called
- [ ] Tests use mocking to isolate wrapper layer
- [ ] Tests follow existing integration test patterns
- [ ] All integration tests passing

**Reference**: Spec lines 751-803

---

### Final Verification

- [ ] Run full test suite
  ```bash
  uv --directory backend run pytest tests/ -v --cov=app
  ```

- [ ] Verify coverage on wrapper module ≥90%
  ```bash
  uv --directory backend run pytest backend/tests/unit/test_garth_wrapper.py -v \
    --cov=app.services.garth_wrapper --cov-report=term-missing --cov-fail-under=90
  ```

- [ ] Verify overall coverage ≥80%
  ```bash
  uv --directory backend run pytest tests/ --cov=app --cov-report=term-missing --cov-fail-under=80
  ```

- [ ] Run code quality checks
  ```bash
  uv run ruff check .
  uv run ruff format --check .
  ```

- [ ] Run security scan
  ```bash
  uv run bandit -c backend/pyproject.toml -r backend/app/services/garth_wrapper.py -ll
  ```

- [ ] Verify no f-strings in logger calls
  ```bash
  grep -n 'logger.*f"' backend/app/services/garth_wrapper.py
  # Should return empty
  ```

- [ ] Verify all imports at top of files
  ```bash
  # Manual inspection of garth_wrapper.py, garmin_client.py, garmin_service.py
  ```

- [ ] Final commit summarizing phase completion
  ```bash
  git add docs/development/garth-wrappers/PHASE_1_plan.md
  git commit -m "docs: Mark Phase 1 complete - wrapper implementation & integration"
  ```

- [ ] Push phase branch
  ```bash
  git push -u origin [current-branch]-phase-1
  ```

- [ ] Create PR into current branch
  ```bash
  gh pr create --base [current-branch] \
    --title "Phase 1: Garth Wrapper Implementation & Integration" \
    --body "Implements typed wrappers for Garth library, removes 8 type: ignore comments, adds comprehensive unit and integration tests."
  ```

---

## Success Criteria

### Technical Deliverables

- [ ] `backend/app/services/garth_wrapper.py` exists (~470 lines)
- [ ] All 9 wrapper functions implemented:
  - [ ] `get_oauth1_token()`
  - [ ] `set_oauth1_token()`
  - [ ] `get_oauth2_token()`
  - [ ] `set_oauth2_token()`
  - [ ] `get_activities_typed()`
  - [ ] `get_daily_summary_typed()`
  - [ ] `get_health_snapshot_typed()`
  - [ ] `get_user_profile_typed()`
- [ ] `backend/tests/unit/test_garth_wrapper.py` exists (~250 lines)
- [ ] All wrapper functions have complete docstrings (Args/Returns/Raises/Note)
- [ ] `garmin_client.py` updated (7 locations, 7 type: ignore removed)
- [ ] `garmin_service.py` updated (1 location, 1 type: ignore removed)
- [ ] Integration tests verify wrappers are called

### Quality Metrics

- [ ] All unit tests passing (existing + new)
- [ ] All integration tests passing (existing + new)
- [ ] Coverage ≥90% on `garth_wrapper.py`
- [ ] Coverage ≥80% overall maintained
- [ ] Ruff linting passes
- [ ] Ruff formatting passes
- [ ] Bandit security scan passes
- [ ] No f-strings in logger calls
- [ ] All imports at top of files
- [ ] All exception logging uses `redact_for_logging()`

### Type Safety Metrics

- [ ] Zero Garth-related `type: ignore` comments in garmin_client.py
- [ ] Zero Garth-related `type: ignore` comments in garmin_service.py
- [ ] No direct `garth.client` access in service files (except tests)
- [ ] Wrapper module ready for mypy strict mode (verified in Phase 2)

---

## Notes

**Design Decisions**:
- **Synchronous wrappers**: Garth is synchronous, callers use `asyncio.to_thread()` for async
- **Non-blocking validation**: Warnings logged, raw data returned (allows recovery from API changes)
- **Model reuse**: Import existing Pydantic models, no duplication
- **Security critical**: ALL logging uses `redact_for_logging()` (enforced by pre-commit hooks)

**Common Patterns from Spec**:
- Validation: `try: Model.validate() except ValidationError: logger.warning(redact())`
- Return types: `dict[str, Any]` for flexibility
- Extra fields: `model_config = {"extra": "allow"}` for forward compatibility
- Documentation: Complete docstrings with Args/Returns/Raises/Note sections

**Integration Points**:
- `garmin_client.py` lines 79, 80, 96, 97, 156, 200, 227
- `garmin_service.py` line 198
- Verify with: `grep -n "type: ignore" backend/app/services/garmin_*.py`

**Testing Strategy**:
- Unit tests: Mock `garth` module, test wrapper validation logic
- Integration tests: Mock wrappers, verify callers use them
- No E2E tests: Internal refactoring, existing E2E tests must pass unchanged

---

## Dependencies for Next Phase

Phase 2 requires:
- [ ] All wrapper functions implemented and tested
- [ ] All integration points updated
- [ ] All type: ignore comments removed
- [ ] Unit test coverage ≥90% on wrapper module
- [ ] All existing tests still passing

Phase 2 will focus on:
- Running mypy on all affected files
- Final quality checks (ruff, bandit, formatting)
- Comprehensive verification of type safety improvements
- Documentation updates
