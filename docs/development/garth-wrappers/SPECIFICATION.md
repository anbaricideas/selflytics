# Garth Wrapper Functions Specification

**Version:** 1.0
**Date:** 2025-11-15
**Status:** Draft
**Related Issue:** #10

## Overview

### Current State

The Selflytics application integrates with Garmin Connect via the [Garth](https://github.com/matin/garth) library, which provides a Python interface to Garmin's OAuth and data APIs. However, Garth lacks type stubs, requiring extensive use of `type: ignore` comments throughout the codebase:

**Affected locations:**
- `backend/app/services/garmin_client.py` - 6 occurrences (lines 79, 96, 97, 156, 200, 227)
- `backend/app/services/garmin_service.py` - 1 occurrence (line 198 - should have type: ignore[attr-defined])

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

### Validation Models

**Design Decision:** Reuse existing Pydantic models from `app.models.garmin_data` instead of creating duplicates. This ensures:
- Single source of truth for data structures
- No field name synchronization issues
- Easier maintenance

**Token validation models** (new - no existing models for tokens):

```python
# File: backend/app/services/garth_wrapper.py

import asyncio
import logging
from typing import Any

import garth
from pydantic import BaseModel, ValidationError
from telemetry.logging_utils import redact_for_logging

from app.models.garmin_data import DailyMetrics, GarminActivity, HealthSnapshot

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


class GarthProfileResponse(BaseModel):
    """Minimal schema for user profile data from Garth."""

    displayName: str | None = None
    model_config = {"extra": "allow"}
```

**Data validation:** Use existing models from `app.models.garmin_data`:
- `GarminActivity` - validates activity responses
- `DailyMetrics` - validates daily summary responses
- `HealthSnapshot` - validates health snapshot responses

**Note:** Existing models use Python naming conventions (snake_case) with Pydantic aliases for Garth's camelCase fields.

### Wrapper Functions

**Design Decision:** All wrappers are synchronous (not async) because:
1. Garth library is synchronous
2. Callers already use `asyncio.to_thread()` for async compatibility
3. Keeps wrapper layer thin and focused on validation only

#### Token Operations

```python
def get_oauth1_token() -> dict[str, Any]:
    """
    Get OAuth1 token from garth.client with type safety.

    Returns:
        OAuth1 token dictionary with validated structure

    Raises:
        AttributeError: If garth.client.oauth1_token not available

    Note:
        Logs warning if token structure changes but returns raw data
    """
    raw_token = garth.client.oauth1_token

    # Validate structure (non-blocking)
    try:
        GarthOAuth1Token.model_validate(raw_token)
    except ValidationError as e:
        logger.warning(
            "Garth OAuth1 token structure changed: %s",
            redact_for_logging(str(e)),
        )

    return raw_token


def set_oauth1_token(token: dict[str, Any]) -> None:
    """
    Set OAuth1 token on garth.client with type validation.

    Args:
        token: OAuth1 token dictionary

    Note:
        Logs warning if token structure unexpected but still sets token.
        Non-blocking approach allows recovery from minor schema changes.
    """
    # Validate before setting (non-blocking)
    try:
        GarthOAuth1Token.model_validate(token)
    except ValidationError as e:
        logger.warning(
            "Setting possibly invalid OAuth1 token: %s",
            redact_for_logging(str(e)),
        )

    garth.client.oauth1_token = token


def get_oauth2_token() -> dict[str, Any]:
    """
    Get OAuth2 token from garth.client with type safety.

    Returns:
        OAuth2 token dictionary with validated structure

    Raises:
        AttributeError: If garth.client.oauth2_token not available

    Note:
        Logs warning if token structure changes but returns raw data
    """
    raw_token = garth.client.oauth2_token

    # Validate structure (non-blocking)
    try:
        GarthOAuth2Token.model_validate(raw_token)
    except ValidationError as e:
        logger.warning(
            "Garth OAuth2 token structure changed: %s",
            redact_for_logging(str(e)),
        )

    return raw_token


def set_oauth2_token(token: dict[str, Any]) -> None:
    """
    Set OAuth2 token on garth.client with type validation.

    Args:
        token: OAuth2 token dictionary

    Note:
        Logs warning if token structure unexpected but still sets token.
        Non-blocking approach allows recovery from minor schema changes.
    """
    # Validate before setting (non-blocking)
    try:
        GarthOAuth2Token.model_validate(token)
    except ValidationError as e:
        logger.warning(
            "Setting possibly invalid OAuth2 token: %s",
            redact_for_logging(str(e)),
        )

    garth.client.oauth2_token = token
```

#### Data Retrieval Operations

```python
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
        Logs warning if Garth response structure changes, but returns raw data.
        Uses existing GarminActivity model for validation.
    """
    raw_activities = garth.activities(date_str)

    # Validate structure of each activity using existing model
    try:
        for activity in raw_activities:
            GarminActivity(**activity)
    except ValidationError as e:
        logger.warning(
            "Garth activities response structure changed for %s: %s",
            date_str,
            redact_for_logging(str(e)),
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
        Logs warning if Garth response structure changes, but returns raw data.
        Validates against expected DailyMetrics fields (steps, distanceMeters, etc.).
    """
    raw_summary = garth.daily_summary(date_str)

    # Validate structure - DailyMetrics expects specific field names
    try:
        # Create temporary DailyMetrics to validate structure
        from datetime import date

        DailyMetrics(
            date=date.fromisoformat(date_str),
            steps=raw_summary.get("steps"),
            distance_meters=raw_summary.get("distanceMeters"),
            active_calories=raw_summary.get("activeCalories"),
            resting_heart_rate=raw_summary.get("restingHeartRate"),
            max_heart_rate=raw_summary.get("maxHeartRate"),
            avg_stress_level=raw_summary.get("avgStressLevel"),
            sleep_seconds=raw_summary.get("sleepSeconds"),
        )
    except ValidationError as e:
        logger.warning(
            "Garth daily_summary response structure changed for %s: %s",
            date_str,
            redact_for_logging(str(e)),
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
        Logs warning if Garth response structure changes, but returns raw data.
        Validates against HealthSnapshot expected fields.
    """
    raw_snapshot = garth.health_snapshot()

    # Validate structure
    try:
        from datetime import UTC, datetime

        HealthSnapshot(
            timestamp=datetime.now(UTC),
            heart_rate=raw_snapshot.get("heartRate"),
            respiration_rate=raw_snapshot.get("respirationRate"),
            stress_level=raw_snapshot.get("stressLevel"),
            spo2=raw_snapshot.get("spo2"),
        )
    except ValidationError as e:
        logger.warning(
            "Garth health_snapshot response structure changed: %s",
            redact_for_logging(str(e)),
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
        Logs warning if Garth response structure changes, but returns raw data.
        According to garmin_service.py:198, garth.client.profile is a dict.
    """
    raw_profile = garth.client.profile

    # Validate structure
    try:
        GarthProfileResponse.model_validate(raw_profile)
    except ValidationError as e:
        logger.warning(
            "Garth profile structure changed: %s",
            redact_for_logging(str(e)),
        )

    return raw_profile
```

### Integration with Existing Code

#### Update `garmin_client.py`

**Before:**
```python
# Line 79
garth.client.oauth1_token = oauth1  # type: ignore[assignment]

# Line 80 (missing type: ignore - should be added)
garth.client.oauth2_token = oauth2

# Line 96
oauth1_encrypted = encrypt_token(garth.client.oauth1_token)  # type: ignore[arg-type]

# Line 97
oauth2_encrypted = encrypt_token(garth.client.oauth2_token)  # type: ignore[arg-type]

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

# Line 79-80 - Type safe token setting
set_oauth1_token(oauth1)
set_oauth2_token(oauth2)

# Line 96-97 - Type safe token reading
oauth1_encrypted = encrypt_token(get_oauth1_token())
oauth2_encrypted = encrypt_token(get_oauth2_token())

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
# Line 198 (should have type: ignore[attr-defined])
display_name: str = garth.client.profile.get("displayName", "User")
```

**After:**
```python
from app.services.garth_wrapper import get_user_profile_typed

# Line 198 - Type safe profile access
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
| **Token structure invalid** | Log warning on both set/get | Consistent non-blocking approach; allows recovery from old/malformed tokens |

### Logging Examples

```python
from telemetry.logging_utils import redact_for_logging

# Warning: Garth changed response structure
logger.warning(
    "Garth activities response structure changed for %s: %s",
    date_str,
    redact_for_logging(str(e)),
)
# Application continues with raw data

# Warning: Token structure unexpected but non-blocking
try:
    set_oauth1_token(bad_token)
except ValidationError as e:
    logger.warning(
        "Setting possibly invalid OAuth1 token: %s",
        redact_for_logging(str(e)),
    )
# Token still set - allows recovery from minor schema changes
```

---

## Testing Strategy

### Unit Tests

Create `backend/tests/unit/test_garth_wrapper.py`:

```python
import pytest
from datetime import date
from unittest.mock import Mock, patch
from pydantic import ValidationError

from app.models.garmin_data import GarminActivity
from app.services.garth_wrapper import (
    get_oauth1_token,
    set_oauth1_token,
    get_activities_typed,
)


class TestTokenOperations:
    """Test OAuth token getter/setter wrappers."""

    @patch("app.services.garth_wrapper.garth")
    def test_get_oauth1_token_valid(self, mock_garth):
        """Should return token when structure valid."""
        mock_garth.client.oauth1_token = {
            "oauth_token": "token123",
            "oauth_token_secret": "secret456",
        }

        token = get_oauth1_token()

        assert token["oauth_token"] == "token123"
        assert token["oauth_token_secret"] == "secret456"

    @patch("app.services.garth_wrapper.garth")
    def test_get_oauth1_token_extra_fields(self, mock_garth, caplog):
        """Should accept extra fields without warning."""
        mock_garth.client.oauth1_token = {
            "oauth_token": "token123",
            "oauth_token_secret": "secret456",
            "new_field": "unexpected",  # Garth added new field
        }

        token = get_oauth1_token()

        # Should still return token
        assert token["oauth_token"] == "token123"
        # No warning - extra fields allowed by model config
        assert "structure changed" not in caplog.text

    @patch("app.services.garth_wrapper.garth")
    def test_set_oauth1_token_invalid(self, mock_garth, caplog):
        """Should log warning but still set token for invalid structure."""
        invalid_token = {"missing": "required_fields"}

        # Should not raise - non-blocking approach
        set_oauth1_token(invalid_token)

        # Should log warning with redacted exception
        assert "possibly invalid" in caplog.text
        # Token should still be set
        assert mock_garth.client.oauth1_token == invalid_token


class TestDataRetrieval:
    """Test data retrieval wrappers."""

    @patch("app.services.garth_wrapper.garth")
    def test_get_activities_typed_valid(self, mock_garth):
        """Should return activities when structure valid."""
        # Use actual GarminActivity-compatible data
        mock_garth.activities.return_value = [
            {
                "activityId": 123,
                "activityName": "Morning Run",
                "activityType": "running",
                "startTimeLocal": "2025-11-15T06:00:00",
            }
        ]

        activities = get_activities_typed("2025-11-15")

        assert len(activities) == 1
        assert activities[0]["activityId"] == 123
        mock_garth.activities.assert_called_once_with("2025-11-15")

    @patch("app.services.garth_wrapper.garth")
    def test_get_activities_typed_missing_required(self, mock_garth, caplog):
        """Should warn if required fields missing."""
        mock_garth.activities.return_value = [
            {
                "activityId": 123,
                # Missing: activityName, activityType, startTimeLocal (required by GarminActivity)
            }
        ]

        activities = get_activities_typed("2025-11-15")

        # Should still return data (non-blocking)
        assert len(activities) == 1
        # Should log warning
        assert "structure changed" in caplog.text

    @patch("app.services.garth_wrapper.garth")
    def test_get_activities_typed_invalid_type(self, mock_garth, caplog):
        """Should warn but return data if field type wrong."""
        mock_garth.activities.return_value = [
            {
                "activityId": "not-an-int",  # Wrong type
                "activityName": "Run",
                "activityType": "running",
                "startTimeLocal": "2025-11-15T06:00:00",
            }
        ]

        activities = get_activities_typed("2025-11-15")

        # Should still return data
        assert len(activities) == 1
        # Should log warning with redacted exception
        assert "structure changed" in caplog.text
```

### Integration Tests

Add verification tests in `backend/tests/integration/test_garmin_client.py`:

```python
from unittest.mock import patch
import pytest
from datetime import date

from app.services.garmin_client import GarminClient


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
            "startTimeLocal": "2025-11-15T06:00:00",
        }
    ]

    client = GarminClient(user_id="test-user")

    # Call should use wrapper
    activities = await client.get_activities(
        start_date=date(2025, 11, 15), end_date=date(2025, 11, 15)
    )

    # Verify wrapper was called (not raw garth.activities)
    mock_get_activities.assert_called()
    assert len(activities) > 0


@pytest.mark.asyncio
@patch("app.services.garth_wrapper.set_oauth1_token")
@patch("app.services.garth_wrapper.set_oauth2_token")
async def test_garmin_client_uses_token_wrappers(
    mock_set_oauth2, mock_set_oauth1, mock_firestore
):
    """Verify GarminClient sets tokens via typed wrappers."""
    client = GarminClient(user_id="test-user")

    # Authenticate should use token setters
    # (assuming authenticate method updated to use wrappers)
    with patch("app.services.garth_wrapper.garth.login"):
        await client.authenticate("user@example.com", "password")

    # Verify wrappers were called
    mock_set_oauth1.assert_called_once()
    mock_set_oauth2.assert_called_once()
```

### Mypy Type Checking

After implementation, verify with:

```bash
# Verify wrapper module passes mypy
uv --directory backend run mypy backend/app/services/garth_wrapper.py --strict

# Verify integration files have no Garth-related type: ignore comments
uv --directory backend run mypy backend/app/services/garmin_client.py
uv --directory backend run mypy backend/app/services/garmin_service.py

# Search for remaining type: ignore comments
grep -n "type: ignore" backend/app/services/garmin_client.py backend/app/services/garmin_service.py
```

**Expected result:**
- Mypy passes on all three files with zero errors
- `grep` finds no `type: ignore` comments related to Garth operations (lines 79, 80, 96, 97, 156, 200, 227 in garmin_client.py; line 198 in garmin_service.py)
- Any remaining `type: ignore` comments are unrelated to Garth integration

---

## Migration Plan

### Phase 1: Create Wrapper Module (1 hour)

**Deliverables:**
1. Create `backend/app/services/garth_wrapper.py`
2. Implement token validation models (GarthOAuth1Token, GarthOAuth2Token, GarthProfileResponse)
3. Import existing data models (GarminActivity, DailyMetrics, HealthSnapshot)
4. Implement token operation wrappers (get/set for oauth1 and oauth2)
5. Implement data retrieval wrappers (activities, daily_summary, health_snapshot, profile)

**Verification:**
- [ ] File exists: `ls -la backend/app/services/garth_wrapper.py`
- [ ] Imports resolve: `python -c "from app.services.garth_wrapper import get_oauth1_token, get_activities_typed"`
- [ ] Mypy passes: `uv --directory backend run mypy backend/app/services/garth_wrapper.py --strict`
- [ ] All functions have docstrings with Args/Returns/Raises sections

### Phase 2: Update Integration Points (1 hour)

**Deliverables:**
1. Update `garmin_client.py` to use wrappers (7 locations: lines 79, 80, 96, 97, 156, 200, 227)
2. Update `garmin_service.py` to use wrappers (1 location: line 198)
3. Remove all Garth-related `type: ignore` comments

**Verification:**
- [ ] Imports added: `grep "from app.services.garth_wrapper import" backend/app/services/garmin_client.py backend/app/services/garmin_service.py`
- [ ] No direct garth.client access: `grep -n "garth.client" backend/app/services/garmin_client.py backend/app/services/garmin_service.py` returns empty
- [ ] No Garth type: ignore: `grep -n "type: ignore" backend/app/services/garmin_client.py backend/app/services/garmin_service.py | grep -E "(garth|oauth|activities|daily_summary|health_snapshot|profile)"` returns empty
- [ ] Mypy passes: `uv --directory backend run mypy backend/app/services/garmin_client.py backend/app/services/garmin_service.py`

### Phase 3: Testing (30 minutes)

**Deliverables:**
1. Create `backend/tests/unit/test_garth_wrapper.py`
2. Write unit tests for all wrapper functions (token ops + data retrieval)
3. Add integration tests verifying wrappers are used

**Verification:**
- [ ] Test file exists: `ls -la backend/tests/unit/test_garth_wrapper.py`
- [ ] Coverage ≥90%: `uv --directory backend run pytest backend/tests/unit/test_garth_wrapper.py -v --cov=app.services.garth_wrapper --cov-report=term-missing --cov-fail-under=90`
- [ ] All unit tests pass: `uv --directory backend run pytest backend/tests/unit/test_garth_wrapper.py -v`
- [ ] All existing tests pass: `uv --directory backend run pytest backend/tests/ -v`
- [ ] No new test failures: Compare test count before/after

### Phase 4: Documentation & Review (30 minutes)

**Deliverables:**
1. Verify all wrapper functions have complete docstrings
2. Update this specification with implementation notes if needed
3. Run code quality checks

**Verification:**
- [ ] All functions documented: `grep -A 2 "^def " backend/app/services/garth_wrapper.py | grep '"""'` shows docstrings for all functions
- [ ] Linting passes: `uv run ruff check backend/app/services/garth_wrapper.py`
- [ ] Formatting passes: `uv run ruff format --check backend/app/services/garth_wrapper.py`
- [ ] Security scan passes: `uv run bandit -c backend/pyproject.toml -r backend/app/services/garth_wrapper.py -ll`
- [ ] No f-strings in logging: `grep -n 'logger.*f"' backend/app/services/garth_wrapper.py` returns empty

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

6. **Garth type stubs package:**
   - Create `garth-stubs` package with `.pyi` type stub files
   - Contribute back to Garth project or publish separately
   - Would eliminate need for runtime validation overhead
   - More sustainable long-term solution than wrappers
   - Reference: [PEP 561](https://www.python.org/dev/peps/pep-0561/) for distributing type information

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
| 1.1 | 2025-11-16 | Claude | Updated with security, consistency, and quality improvements |

---

## Approval & Sign-off

**Stakeholders:**
- [ ] Product Owner: _______________ Date: _______
- [ ] Tech Lead: _______________ Date: _______

**Implementation Start Date:** TBD
**Target Completion Date:** TBD (Est. 2-3 hours)

---

*End of Specification*

---

## Appendix C: Changes from Version 1.0

### Summary of Improvements (Version 1.1)

This section documents the improvements made to the original specification:

#### 1. **Security: Added PII Redaction** (Critical)
- **Issue:** Logging exceptions without redaction violates project security policy
- **Fix:** Added `from telemetry.logging_utils import redact_for_logging` to imports
- **Impact:** All exception logging now uses `redact_for_logging(str(e))` to prevent PII leakage
- **Affected:** Lines 205, 276, 299, 326, 349, 385, 429, 465, 492 (all logger calls)

#### 2. **Design: Reuse Existing Pydantic Models** (Critical)
- **Issue:** Specification created duplicate models (GarthActivityResponse, GarthDailySummaryResponse, GarthHealthSnapshotResponse) with inconsistent field names
- **Fix:** Import and reuse existing models from `app.models.garmin_data`:
  - `GarminActivity` (with field aliases for camelCase)
  - `DailyMetrics`
  - `HealthSnapshot`
- **Impact:** Single source of truth, no field name synchronization issues
- **Affected:** Lines 187-243 (validation models section)

#### 3. **Design: Non-Blocking Token Setters** (Medium)
- **Issue:** Original spec had token setters raise ValidationError, contradicting non-blocking philosophy
- **Fix:** Token setters now log warnings but still set tokens (consistent with getters)
- **Rationale:** Allows recovery from old/malformed tokens; prevents breaking on minor schema changes
- **Affected:** Lines 282-302, 332-352, 595 (error scenarios table)

#### 4. **Accuracy: Fixed Line Number References** (Medium)
- **Issue:** Spec listed line 89 instead of 97 for oauth2 encryption
- **Fix:** Corrected to lines 79, 96, 97, 156, 200, 227 in garmin_client.py
- **Added:** Note that line 80 (oauth2_token assignment) is missing type: ignore
- **Affected:** Lines 15-16, 503-525 (affected locations and integration examples)

#### 5. **Design: Clarified Sync/Async Strategy** (Medium)
- **Issue:** Unclear whether wrappers should be async or sync
- **Decision:** Wrappers are synchronous; callers use `asyncio.to_thread()` for async compatibility
- **Rationale:** Keeps wrapper layer thin; Garth is synchronous; maintains existing async patterns
- **Affected:** Lines 247-250 (added design decision note)

#### 6. **Testing: Improved Test Examples** (Medium)
- **Fixed:** Token setter tests no longer expect ValidationError (now expects warning logs)
- **Fixed:** Activity validation uses actual GarminActivity model with correct fields
- **Added:** Integration tests with mocks to verify wrappers are actually called
- **Affected:** Lines 629-803 (unit and integration test sections)

#### 7. **Verification: Specific Commands** (Medium)
- **Issue:** Vague verification criteria ("imports resolve correctly")
- **Fix:** Added exact shell commands for every verification step
- **Examples:**
  - `ls -la backend/app/services/garth_wrapper.py`
  - `uv --directory backend run mypy backend/app/services/garth_wrapper.py --strict`
  - `grep -n "type: ignore" backend/app/services/garmin_client.py`
- **Affected:** Lines 839-884 (all phase verification sections)

#### 8. **Documentation: Added Type Stubs Future Enhancement** (Low)
- **Added:** Section suggesting creation of `garth-stubs` package as long-term solution
- **Rationale:** More sustainable than runtime validation; could contribute back to Garth project
- **Affected:** Lines 937-942 (future enhancements)

#### 9. **Consistency: Updated Error Handling Documentation** (Low)
- **Fixed:** Error handling examples now use redact_for_logging
- **Fixed:** Token setter example no longer shows "fail fast" approach
- **Affected:** Lines 597-619 (logging examples)

#### 10. **Quality: Enhanced Mypy Verification** (Low)
- **Added:** `--strict` flag for wrapper module verification
- **Added:** `grep` command to verify all type: ignore comments removed
- **Added:** Clear expected results documentation
- **Affected:** Lines 807-824 (mypy verification section)

### Design Philosophy Clarifications

The updated specification emphasizes:

1. **Security First:** All exception logging must use `redact_for_logging()` (enforced by pre-commit hooks)
2. **DRY Principle:** Reuse existing Pydantic models rather than creating duplicates
3. **Non-Blocking Validation:** Log warnings, return data (applies to ALL wrappers, including setters)
4. **Verifiable Quality:** Every verification step has an exact, executable command
5. **Project Consistency:** Follows Selflytics patterns (telemetry, async, model reuse)
