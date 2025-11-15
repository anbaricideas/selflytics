# Garth Wrapper Functions Specification

**Version:** 1.0
**Date:** 2025-11-15
**Status:** Draft
**Related Issue:** #10

## Overview

### Current State

The Selflytics application integrates with Garmin Connect via the [Garth](https://github.com/matin/garth) library, which provides a Python interface to Garmin's OAuth and data APIs. However, Garth lacks type stubs, requiring extensive use of `type: ignore` comments throughout the codebase:

**Affected locations:**
- `backend/app/services/garmin_client.py` - 6 occurrences (lines 79, 89, 96, 156, 200, 227)
- `backend/app/services/garmin_service.py` - 1 occurrence (line 198)

**Current approach:**
```python
# Type checking disabled - no runtime validation
garth.client.oauth1_token = oauth1  # type: ignore[assignment]
garth.client.oauth2_token = oauth2  # type: ignore[attr-defined]
day_activities = await asyncio.to_thread(garth.activities, current_date.isoformat())  # type: ignore[attr-defined]
```

**Problems:**
1. **Masked type errors:** Mypy cannot verify correct usage of Garth APIs
2. **Silent API changes:** If Garth modifies response structures, no alerts until runtime
3. **Poor documentation:** Type signatures unclear for future maintainers
4. **Limited debugging:** No validation that responses match expected structure

### Desired State

Create a typed wrapper layer around critical Garth operations with:

1. **Explicit type signatures:** Remove all `type: ignore` comments
2. **Runtime validation:** Pydantic models validate Garth responses
3. **Early detection:** Log warnings when Garth API changes detected
4. **Self-documenting:** Clear types document expected data structures

**Approach:**
```python
# Typed wrapper with runtime validation
from app.services.garth_wrapper import get_activities_typed, GarthActivityResponse

activities = await get_activities_typed(start_date, end_date)
# Type: list[dict[str, Any]] - validated against GarthActivityResponse schema
```

### Goals and Objectives

**Primary Goals:**
- **Type Safety:** Eliminate 7+ `type: ignore` comments across codebase
- **Runtime Validation:** Detect Garth API changes before silent data corruption
- **Maintainability:** Clear type signatures for future development

**Secondary Goals:**
- **Documentation:** Pydantic models serve as executable API documentation
- **Debugging Support:** Better error messages when integration issues occur
- **Testability:** Easier to mock and test Garth interactions

**Non-Goals:**
- Replace Garth entirely (not forking/wrapping the entire library)
- Add caching or rate limiting (handled by existing layers)
- Change existing service layer APIs (internal refactoring only)

---

## Design Decisions Summary

| Aspect | Decision | Rationale |
|--------|----------|-----------|
| **Wrapper location** | `backend/app/services/garth_wrapper.py` | Co-located with other Garmin services; clear separation of concerns |
| **Validation approach** | Pydantic models with `.model_validate()` | Consistent with project patterns; fails fast on schema mismatch |
| **Error handling** | Log warnings, return raw data | Non-blocking: allows app to continue if Garth changes non-critical fields |
| **Type hints** | `dict[str, Any]` return types | Preserves flexibility; validated structure documented via Pydantic models |
| **Async compatibility** | All wrappers accept/return async-compatible types | Maintains FastAPI async patterns throughout |
| **Token operations** | Getter/setter functions | Encapsulates type-unsafe attribute access to `garth.client` |

---

## Garth API Analysis

### Current Garth Usage Patterns

From codebase analysis, we use these Garth operations:

#### 1. OAuth Token Management
```python
# Reading tokens
oauth1 = garth.client.oauth1_token  # type: ignore[attr-defined]
oauth2 = garth.client.oauth2_token  # type: ignore[attr-defined]

# Writing tokens
garth.client.oauth1_token = oauth1  # type: ignore[assignment]
garth.client.oauth2_token = oauth2  # type: ignore[assignment]

# Profile access
display_name = garth.client.profile.get("displayName", "User")  # type: ignore[attr-defined]
```

#### 2. Activity Retrieval
```python
day_activities = await asyncio.to_thread(
    garth.activities,
    current_date.isoformat()
)  # type: ignore[attr-defined]
```

#### 3. Daily Summaries
```python
summary = await asyncio.to_thread(
    garth.daily_summary,
    target_date.isoformat()
)  # type: ignore[attr-defined]
```

#### 4. Health Snapshots
```python
health_data = await asyncio.to_thread(
    garth.health_snapshot
)  # type: ignore[attr-defined]
```

### Expected Garth Response Structures

Based on existing Pydantic models in `backend/app/models/garmin_data.py`:

**Activities:**
```json
{
  "activityId": 12345678,
  "activityName": "Morning Run",
  "activityType": "running",
  "startTimeGMT": "2025-11-15T06:00:00Z",
  "duration": 3600,
  "distance": 10000,
  "calories": 650
}
```

**Daily Summary:**
```json
{
  "steps": 12543,
  "distanceMeters": 8432,
  "activeCalories": 456,
  "restingHeartRate": 58,
  "maxHeartRate": 165,
  "avgStressLevel": 32,
  "sleepSeconds": 28800
}
```

**Health Snapshot:**
```json
{
  "heartRate": 72,
  "respirationRate": 14,
  "stressLevel": 28,
  "spo2": 98
}
```

**OAuth Tokens:**
```python
{
  "oauth_token": "...",
  "oauth_token_secret": "...",
  # ... other fields
}
```

---

## Technical Implementation

### File Structure

```
backend/app/services/
├── garmin_client.py         # Existing - uses wrappers
├── garmin_service.py        # Existing - uses wrappers
└── garth_wrapper.py         # NEW - typed wrapper functions
```

### Pydantic Validation Models

Create minimal validation models to detect breaking changes:

```python
# File: backend/app/services/garth_wrapper.py

from typing import Any
from pydantic import BaseModel, Field, ValidationError
import logging

logger = logging.getLogger(__name__)


class GarthOAuth1Token(BaseModel):
    """Minimal schema for OAuth1 token structure."""
    oauth_token: str
    oauth_token_secret: str
    # Allow additional fields Garth may include
    model_config = {"extra": "allow"}


class GarthOAuth2Token(BaseModel):
    """Minimal schema for OAuth2 token structure."""
    access_token: str
    token_type: str = "Bearer"
    expires_in: int | None = None
    refresh_token: str | None = None
    model_config = {"extra": "allow"}


class GarthActivityResponse(BaseModel):
    """Minimal schema for activity data from Garth."""
    activityId: int = Field(..., description="Unique activity identifier")
    activityName: str = Field(..., description="User-assigned activity name")
    activityType: str | None = Field(None, description="Activity type (running, cycling, etc.)")
    startTimeGMT: str | None = Field(None, description="Activity start time (ISO format)")
    duration: float | None = Field(None, description="Duration in seconds")
    distance: float | None = Field(None, description="Distance in meters")
    calories: int | None = Field(None, description="Calories burned")
    model_config = {"extra": "allow"}


class GarthDailySummaryResponse(BaseModel):
    """Minimal schema for daily summary data from Garth."""
    # Optional fields - Garth may return partial data
    steps: int | None = None
    distanceMeters: float | None = None
    activeCalories: int | None = None
    restingHeartRate: int | None = None
    maxHeartRate: int | None = None
    avgStressLevel: int | None = None
    sleepSeconds: int | None = None
    model_config = {"extra": "allow"}


class GarthHealthSnapshotResponse(BaseModel):
    """Minimal schema for health snapshot data from Garth."""
    heartRate: int | None = None
    respirationRate: int | None = None
    stressLevel: int | None = None
    spo2: int | None = None
    model_config = {"extra": "allow"}


class GarthProfileResponse(BaseModel):
    """Minimal schema for user profile data from Garth."""
    displayName: str | None = None
    model_config = {"extra": "allow"}
```

### Wrapper Functions

#### Token Operations

```python
import garth
from typing import Any


def get_oauth1_token() -> dict[str, Any]:
    """
    Get OAuth1 token from garth.client with type safety.

    Returns:
        OAuth1 token dictionary with validated structure

    Raises:
        AttributeError: If garth.client.oauth1_token not available
        ValidationError: If token structure doesn't match expected schema
    """
    raw_token = garth.client.oauth1_token

    # Validate structure
    try:
        GarthOAuth1Token.model_validate(raw_token)
    except ValidationError as e:
        logger.warning(
            "Garth OAuth1 token structure changed: %s",
            str(e)
        )

    return raw_token


def set_oauth1_token(token: dict[str, Any]) -> None:
    """
    Set OAuth1 token on garth.client with type validation.

    Args:
        token: OAuth1 token dictionary

    Raises:
        ValidationError: If token structure invalid
    """
    # Validate before setting
    GarthOAuth1Token.model_validate(token)
    garth.client.oauth1_token = token


def get_oauth2_token() -> dict[str, Any]:
    """
    Get OAuth2 token from garth.client with type safety.

    Returns:
        OAuth2 token dictionary with validated structure

    Raises:
        AttributeError: If garth.client.oauth2_token not available
        ValidationError: If token structure doesn't match expected schema
    """
    raw_token = garth.client.oauth2_token

    # Validate structure
    try:
        GarthOAuth2Token.model_validate(raw_token)
    except ValidationError as e:
        logger.warning(
            "Garth OAuth2 token structure changed: %s",
            str(e)
        )

    return raw_token


def set_oauth2_token(token: dict[str, Any]) -> None:
    """
    Set OAuth2 token on garth.client with type validation.

    Args:
        token: OAuth2 token dictionary

    Raises:
        ValidationError: If token structure invalid
    """
    # Validate before setting
    GarthOAuth2Token.model_validate(token)
    garth.client.oauth2_token = token
```

#### Data Retrieval Operations

```python
from datetime import date


def get_activities_typed(date_str: str) -> list[dict[str, Any]]:
    """
    Fetch activities for a specific date with runtime type validation.

    Args:
        date_str: Date in ISO format (YYYY-MM-DD)

    Returns:
        List of activity dictionaries with validated structure

    Raises:
        Exception: If Garth API call fails

    Note:
        Logs warning if Garth response structure changes, but returns raw data
    """
    raw_activities = garth.activities(date_str)

    # Validate structure of each activity
    try:
        for activity in raw_activities:
            GarthActivityResponse.model_validate(activity)
    except ValidationError as e:
        logger.warning(
            "Garth activities response structure changed for %s: %s",
            date_str,
            str(e)
        )

    return raw_activities


def get_daily_summary_typed(date_str: str) -> dict[str, Any]:
    """
    Fetch daily summary for a specific date with runtime type validation.

    Args:
        date_str: Date in ISO format (YYYY-MM-DD)

    Returns:
        Daily summary dictionary with validated structure

    Raises:
        Exception: If Garth API call fails

    Note:
        Logs warning if Garth response structure changes, but returns raw data
    """
    raw_summary = garth.daily_summary(date_str)

    # Validate structure
    try:
        GarthDailySummaryResponse.model_validate(raw_summary)
    except ValidationError as e:
        logger.warning(
            "Garth daily_summary response structure changed for %s: %s",
            date_str,
            str(e)
        )

    return raw_summary


def get_health_snapshot_typed() -> dict[str, Any]:
    """
    Fetch latest health snapshot with runtime type validation.

    Returns:
        Health snapshot dictionary with validated structure

    Raises:
        Exception: If Garth API call fails

    Note:
        Logs warning if Garth response structure changes, but returns raw data
    """
    raw_snapshot = garth.health_snapshot()

    # Validate structure
    try:
        GarthHealthSnapshotResponse.model_validate(raw_snapshot)
    except ValidationError as e:
        logger.warning(
            "Garth health_snapshot response structure changed: %s",
            str(e)
        )

    return raw_snapshot


def get_user_profile_typed() -> dict[str, Any]:
    """
    Get user profile from garth.client with type safety.

    Returns:
        User profile dictionary with validated structure

    Raises:
        AttributeError: If garth.client.profile not available

    Note:
        Logs warning if Garth response structure changes, but returns raw data
    """
    raw_profile = garth.client.profile

    # Validate structure
    try:
        GarthProfileResponse.model_validate(raw_profile)
    except ValidationError as e:
        logger.warning(
            "Garth profile structure changed: %s",
            str(e)
        )

    return raw_profile
```

### Integration with Existing Code

#### Update `garmin_client.py`

**Before:**
```python
# Line 79
garth.client.oauth1_token = oauth1  # type: ignore[assignment]

# Line 96
oauth1_encrypted = encrypt_token(garth.client.oauth1_token)  # type: ignore[arg-type]

# Line 156
day_activities = await asyncio.to_thread(garth.activities, current_date.isoformat())  # type: ignore[attr-defined]

# Line 200
summary = await asyncio.to_thread(garth.daily_summary, target_date.isoformat())  # type: ignore[attr-defined]

# Line 227
health_data = await asyncio.to_thread(garth.health_snapshot)  # type: ignore[attr-defined]
```

**After:**
```python
from app.services.garth_wrapper import (
    get_oauth1_token,
    get_oauth2_token,
    set_oauth1_token,
    set_oauth2_token,
    get_activities_typed,
    get_daily_summary_typed,
    get_health_snapshot_typed,
)

# Line 79 - Type safe token setting
set_oauth1_token(oauth1)

# Line 96 - Type safe token reading
oauth1_encrypted = encrypt_token(get_oauth1_token())

# Line 156 - Type safe activities fetch
day_activities = await asyncio.to_thread(
    get_activities_typed,
    current_date.isoformat()
)

# Line 200 - Type safe daily summary fetch
summary = await asyncio.to_thread(
    get_daily_summary_typed,
    target_date.isoformat()
)

# Line 227 - Type safe health snapshot fetch
health_data = await asyncio.to_thread(get_health_snapshot_typed)
```

#### Update `garmin_service.py`

**Before:**
```python
# Line 198
display_name: str = garth.client.profile.get("displayName", "User")
```

**After:**
```python
from app.services.garth_wrapper import get_user_profile_typed

# Line 198
profile = get_user_profile_typed()
display_name: str = profile.get("displayName", "User")
```

---

## Error Handling Strategy

### Philosophy

**Non-blocking validation:** If Garth changes response structure, log warning but continue operation. This prevents breaking changes in Garth from causing total application failure.

### Error Scenarios

| Scenario | Handling | Rationale |
|----------|----------|-----------|
| **Validation warning** | Log warning, return raw data | Non-critical: app can continue with slightly different schema |
| **Missing required field** | Validation error logged, raw data returned | Pydantic models use optional fields for most attributes |
| **Garth API call fails** | Exception propagates to caller | Critical: cannot proceed without data |
| **Token structure invalid** | Raise `ValidationError` on set, warn on get | Setting bad tokens should fail fast; reading allows degraded operation |

### Logging Examples

```python
# Warning: Garth changed response structure
logger.warning(
    "Garth activities response structure changed for %s: %s",
    date_str,
    str(e)
)
# Application continues with raw data

# Critical: Cannot encrypt invalid token
try:
    set_oauth1_token(bad_token)
except ValidationError as e:
    logger.error("Invalid OAuth1 token structure: %s", str(e))
    raise  # Fail fast - cannot proceed
```

---

## Testing Strategy

### Unit Tests

Create `backend/tests/unit/test_garth_wrapper.py`:

```python
import pytest
from unittest.mock import Mock, patch
from pydantic import ValidationError

from app.services.garth_wrapper import (
    get_oauth1_token,
    set_oauth1_token,
    get_activities_typed,
    GarthActivityResponse,
)


class TestTokenOperations:
    """Test OAuth token getter/setter wrappers."""

    @patch('app.services.garth_wrapper.garth')
    def test_get_oauth1_token_valid(self, mock_garth):
        """Should return token when structure valid."""
        mock_garth.client.oauth1_token = {
            "oauth_token": "token123",
            "oauth_token_secret": "secret456"
        }

        token = get_oauth1_token()

        assert token["oauth_token"] == "token123"
        assert token["oauth_token_secret"] == "secret456"

    @patch('app.services.garth_wrapper.garth')
    def test_get_oauth1_token_extra_fields(self, mock_garth, caplog):
        """Should accept extra fields with warning."""
        mock_garth.client.oauth1_token = {
            "oauth_token": "token123",
            "oauth_token_secret": "secret456",
            "new_field": "unexpected"  # Garth added new field
        }

        token = get_oauth1_token()

        # Should still return token
        assert token["oauth_token"] == "token123"
        # No warning - extra fields allowed
        assert "structure changed" not in caplog.text

    @patch('app.services.garth_wrapper.garth')
    def test_set_oauth1_token_invalid(self, mock_garth):
        """Should raise ValidationError for invalid token."""
        invalid_token = {"missing": "required_fields"}

        with pytest.raises(ValidationError):
            set_oauth1_token(invalid_token)


class TestDataRetrieval:
    """Test data retrieval wrappers."""

    @patch('app.services.garth_wrapper.garth')
    def test_get_activities_typed_valid(self, mock_garth):
        """Should return activities when structure valid."""
        mock_garth.activities.return_value = [
            {
                "activityId": 123,
                "activityName": "Morning Run",
                "activityType": "running"
            }
        ]

        activities = get_activities_typed("2025-11-15")

        assert len(activities) == 1
        assert activities[0]["activityId"] == 123
        mock_garth.activities.assert_called_once_with("2025-11-15")

    @patch('app.services.garth_wrapper.garth')
    def test_get_activities_typed_missing_optional(self, mock_garth):
        """Should accept activities missing optional fields."""
        mock_garth.activities.return_value = [
            {
                "activityId": 123,
                "activityName": "Run",
                # Missing: activityType, duration, etc.
            }
        ]

        activities = get_activities_typed("2025-11-15")

        # Should succeed - optional fields can be missing
        assert len(activities) == 1

    @patch('app.services.garth_wrapper.garth')
    def test_get_activities_typed_invalid_schema(self, mock_garth, caplog):
        """Should warn but return data if schema invalid."""
        mock_garth.activities.return_value = [
            {
                "activityId": "not-an-int",  # Wrong type
                "activityName": "Run"
            }
        ]

        activities = get_activities_typed("2025-11-15")

        # Should still return data
        assert len(activities) == 1
        # Should log warning
        assert "structure changed" in caplog.text
```

### Integration Tests

Update existing integration tests in `backend/tests/integration/test_garmin_client.py`:

```python
@pytest.mark.asyncio
async def test_garmin_client_uses_typed_wrappers(mock_garth_authenticated):
    """Ensure GarminClient uses typed wrappers instead of raw Garth."""
    client = GarminClient(user_id="test-user")

    # Load tokens should use wrappers
    await client.load_tokens()

    # Activities should use wrappers
    activities = await client.get_activities(
        start_date=date(2025, 11, 1),
        end_date=date(2025, 11, 15)
    )

    # Should receive validated data
    assert isinstance(activities, list)
```

### Mypy Type Checking

After implementation, verify with:

```bash
uv --directory backend run mypy backend/app/services/garmin_client.py
uv --directory backend run mypy backend/app/services/garmin_service.py
uv --directory backend run mypy backend/app/services/garth_wrapper.py
```

**Expected result:** Zero `type: ignore` comments remaining in Garmin integration code.

---

## Migration Plan

### Phase 1: Create Wrapper Module (1 hour)

**Deliverables:**
1. Create `backend/app/services/garth_wrapper.py`
2. Implement all Pydantic validation models
3. Implement token operation wrappers
4. Implement data retrieval wrappers

**Verification:**
- [ ] File created with all functions documented
- [ ] Imports resolve correctly
- [ ] Mypy passes on wrapper module

### Phase 2: Update Integration Points (1 hour)

**Deliverables:**
1. Update `garmin_client.py` to use wrappers (6 locations)
2. Update `garmin_service.py` to use wrappers (1 location)
3. Remove all `type: ignore` comments

**Verification:**
- [ ] All imports added
- [ ] All function calls replaced
- [ ] No `type: ignore[attr-defined]` or `type: ignore[assignment]` in Garmin code
- [ ] Mypy passes on both files

### Phase 3: Testing (30 minutes)

**Deliverables:**
1. Create `backend/tests/unit/test_garth_wrapper.py`
2. Write unit tests for all wrapper functions
3. Update integration tests if needed

**Verification:**
- [ ] Unit tests achieve 90%+ coverage on wrapper module
- [ ] All existing Garmin integration tests pass
- [ ] No new test failures introduced

### Phase 4: Documentation & Review (30 minutes)

**Deliverables:**
1. Add docstrings to all wrapper functions
2. Update this specification with actual implementation notes
3. Code review and refinement

**Verification:**
- [ ] All functions documented with Args/Returns/Raises
- [ ] Specification reflects actual implementation
- [ ] Code passes linting (`ruff check`)

---

## Success Criteria

### Functional Requirements

- [ ] All `type: ignore` comments removed from Garmin integration code
- [ ] Mypy passes with no errors on `garmin_client.py` and `garmin_service.py`
- [ ] Pydantic models validate all Garth responses
- [ ] Warnings logged when Garth API structure changes
- [ ] All existing Garmin functionality works unchanged

### Non-Functional Requirements

- [ ] Unit test coverage ≥90% on `garth_wrapper.py`
- [ ] Integration tests pass without modification
- [ ] No performance degradation (validation overhead minimal)
- [ ] Code passes linting and formatting checks

### User Experience Goals

- [ ] No user-facing changes (internal refactoring only)
- [ ] Better error messages if Garth integration breaks
- [ ] Developers can understand Garth API from type signatures

---

## Future Enhancements

### Not in Initial Scope

1. **Stricter validation modes:**
   - Add config flag to fail fast on validation errors (development mode)
   - Production mode continues with warnings (current approach)

2. **Response caching:**
   - Cache validated responses to skip re-validation
   - Requires cache invalidation strategy

3. **Garth version pinning:**
   - Document which Garth version schemas based on
   - Add CI check to alert on Garth version updates

4. **Mock Garth responses:**
   - Provide fixture data matching validation schemas
   - Easier testing without real Garth dependency

5. **Telemetry:**
   - Track validation failures in Cloud Logging
   - Alert on repeated schema mismatches

---

## Appendix A: Garth Library Context

### About Garth

**Repository:** https://github.com/matin/garth
**Purpose:** Unofficial Python library for Garmin Connect API
**Status:** Active development, no type stubs
**License:** MIT

### Why Garth Lacks Type Stubs

Garth is a reverse-engineered library based on Garmin's undocumented APIs. Garmin may change response structures without notice, making static typing difficult. Our wrapper layer adapts to this uncertainty with runtime validation.

### Known Garth Stability Issues

- Response schemas vary by user (e.g., premium vs. free accounts)
- New Garmin features add fields to existing endpoints
- Field names sometimes change (camelCase inconsistencies)

**Our approach:** Validate required fields only; allow extra fields; log changes for review.

---

## Appendix B: Code Coverage Requirements

### Coverage Targets

| Module | Target Coverage | Critical Paths |
|--------|----------------|----------------|
| `garth_wrapper.py` | ≥90% | All wrapper functions, validation logic |
| `garmin_client.py` | ≥80% | Token loading, data retrieval (existing target) |
| `garmin_service.py` | ≥80% | Service methods (existing target) |

### Test Pyramid Distribution

- **Unit tests (60%):** Mock Garth responses, test wrapper validation
- **Integration tests (30%):** Test with real Garth-like responses
- **E2E tests (10%):** Existing Playwright tests (no changes needed)

---

## Change Log

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-11-15 | Claude | Initial specification based on issue #10 |

---

## Approval & Sign-off

**Stakeholders:**
- [ ] Product Owner: _______________ Date: _______
- [ ] Tech Lead: _______________ Date: _______

**Implementation Start Date:** TBD
**Target Completion Date:** TBD (Est. 2-3 hours)

---

*End of Specification*
