# Phase 2: Garmin Integration

**Branch**: `feat/phase-2-garmin`
**Status**: ⬜ TODO
**Estimated Time**: 80 hours (2 weeks)

---

## Goal

Implement production-ready Garmin Connect integration with OAuth authentication, token management, and data caching. This phase enables users to securely link their Garmin accounts and automatically fetch fitness data (activities, metrics, health snapshots) with intelligent caching.

**Key Deliverables**:
- Garmin OAuth flow (MFA supported)
- Secure token storage in Firestore (encrypted with KMS)
- GarminClient service (async wrapper around garth library)
- Data caching layer with TTL (24h for activities, 6h for metrics)
- Pydantic models for Garmin data structures
- Settings page for account linking
- 80%+ test coverage (mocked Garmin API)

---

## Prerequisites

- ✅ Phase 1 completed (authentication, infrastructure)
- ✅ User authentication working (JWT tokens)
- ✅ Firestore configured and accessible
- ✅ Terraform infrastructure deployed
- ✅ Garmin Developer account created (for OAuth credentials)

---

## Deliverables

### Garmin OAuth & Authentication

- ✅ `backend/app/services/garmin_service.py` - OAuth flow management
- ✅ `backend/app/routes/garmin.py` - OAuth endpoints
- ✅ `backend/app/models/garmin_token.py` - Token storage model
- ✅ Settings page: `backend/app/templates/settings_garmin.html`
- ✅ OAuth redirect URI configured in Garmin Developer Portal

### GarminClient Service

- ✅ `backend/app/services/garmin_client.py` - Async garth wrapper
- ✅ Methods: authenticate, get_activities, get_daily_metrics, get_health_snapshot
- ✅ Token management: save, load, refresh
- ✅ Error handling: MFA, rate limits, API errors

### Data Models

- ✅ `backend/app/models/garmin_data.py` - Pydantic models:
  - GarminActivity
  - DailyMetrics
  - HealthSnapshot
  - UserProfile (Garmin-specific)
- ✅ Validation for all Garmin API response fields

### Caching Layer

- ✅ `backend/app/utils/cache.py` - Cache utilities
- ✅ Firestore collection: `garmin_data`
- ✅ TTL implementation: 24h (activities), 6h (metrics), 1h (health)
- ✅ Cache key generation
- ✅ Cache invalidation logic

### Token Encryption

- ✅ KMS integration for token encryption
- ✅ Encrypt tokens before Firestore storage
- ✅ Decrypt tokens when loading

### Tests

- ✅ `backend/tests/unit/test_garmin_client.py` - Client methods
- ✅ `backend/tests/unit/test_garmin_cache.py` - Cache logic
- ✅ `backend/tests/integration/test_garmin_oauth.py` - OAuth flow
- ✅ `backend/tests/integration/test_garmin_data_fetch.py` - Data fetching
- ✅ 80%+ coverage on new code

---

## Implementation Steps

### Setup

- [ ] ⏳ NEXT: Create branch `feat/phase-2-garmin`
- [ ] Review Garmin Agents repository: `/Users/bryn/repos/garmin_agents/`
- [ ] Install garth library: `uv add garth`
- [ ] Register Selflytics app in Garmin Developer Portal
- [ ] Configure OAuth redirect URI: `https://<your-domain>/auth/garmin/callback`

---

### Step 1: Garmin Data Models

**File**: `backend/app/models/garmin_data.py`

- [ ] Write tests first: `backend/tests/unit/test_garmin_models.py`
  - Test GarminActivity model validation
  - Test DailyMetrics model validation
  - Test HealthSnapshot model validation
  - Test field types and optional fields
- [ ] Review tests for quality
- [ ] Verify tests fail (no implementation)
- [ ] Implement Pydantic models for Garmin data:
  ```python
  """Garmin data models based on API responses."""
  from pydantic import BaseModel, Field
  from datetime import datetime, date
  from typing import Optional

  class GarminActivity(BaseModel):
      """Activity from Garmin Connect."""
      activity_id: int = Field(..., alias="activityId")
      activity_name: str = Field(..., alias="activityName")
      activity_type: str = Field(..., alias="activityType")
      start_time_local: datetime = Field(..., alias="startTimeLocal")
      distance_meters: Optional[float] = Field(None, alias="distance")
      duration_seconds: Optional[int] = Field(None, alias="duration")
      average_hr: Optional[int] = Field(None, alias="averageHR")
      calories: Optional[int] = Field(None, alias="calories")
      elevation_gain: Optional[float] = Field(None, alias="elevationGain")

      class Config:
          populate_by_name = True

  class DailyMetrics(BaseModel):
      """Daily summary metrics from Garmin."""
      date: date
      steps: Optional[int] = None
      distance_meters: Optional[float] = None
      active_calories: Optional[int] = None
      resting_heart_rate: Optional[int] = None
      max_heart_rate: Optional[int] = None
      avg_stress_level: Optional[int] = None
      sleep_seconds: Optional[int] = None

  class HealthSnapshot(BaseModel):
      """Real-time health snapshot."""
      timestamp: datetime
      heart_rate: Optional[int] = None
      respiration_rate: Optional[int] = None
      stress_level: Optional[int] = None
      spo2: Optional[float] = None

  class GarminUserProfile(BaseModel):
      """User profile from Garmin Connect."""
      user_id: str
      display_name: str
      email: Optional[str] = None
      profile_image_url: Optional[str] = None
  ```
- [ ] Verify tests pass
- [ ] Commit: "feat: add Garmin data Pydantic models"

**Implementation Reference**: Adapt from garmin_agents models

---

### Step 2: Token Storage Model

**File**: `backend/app/models/garmin_token.py`

- [ ] Write tests first: `backend/tests/unit/test_garmin_token_model.py`
  - Test GarminToken model validation
  - Test encryption fields
  - Test timestamp fields
- [ ] Implement GarminToken model:
  ```python
  """Garmin OAuth token storage model."""
  from pydantic import BaseModel, Field
  from datetime import datetime
  from typing import Optional

  class GarminToken(BaseModel):
      """Garmin OAuth tokens stored in Firestore."""
      user_id: str
      oauth1_token_encrypted: str  # Encrypted before storage
      oauth2_token_encrypted: str  # Encrypted before storage
      token_expiry: Optional[datetime] = None
      last_sync: Optional[datetime] = None
      mfa_enabled: bool = False
      created_at: datetime
      updated_at: datetime

  class GarminTokenDecrypted(BaseModel):
      """Decrypted tokens for use in GarminClient."""
      oauth1_token: dict
      oauth2_token: dict
  ```
- [ ] Verify tests pass
- [ ] Commit: "feat: add GarminToken storage model"

---

### Step 3: Token Encryption Utilities

**File**: `backend/app/utils/encryption.py`

- [ ] Write tests first: `backend/tests/unit/test_encryption.py`
  - Test encrypt_token (produces different output each time)
  - Test decrypt_token (recovers original value)
  - Test round-trip (encrypt → decrypt)
  - Test invalid ciphertext handling
- [ ] Implement KMS encryption functions:
  ```python
  """Token encryption using GCP KMS."""
  from google.cloud import kms
  import base64
  import json

  KMS_KEY_NAME = "projects/selflytics-infra/locations/australia-southeast1/keyRings/selflytics-keys/cryptoKeys/token-encryption"

  def encrypt_token(token_dict: dict) -> str:
      """Encrypt token dictionary using KMS."""
      kms_client = kms.KeyManagementServiceClient()

      # Serialize token
      plaintext = json.dumps(token_dict).encode('utf-8')

      # Encrypt with KMS
      encrypt_response = kms_client.encrypt(
          request={'name': KMS_KEY_NAME, 'plaintext': plaintext}
      )

      # Return base64-encoded ciphertext
      return base64.b64encode(encrypt_response.ciphertext).decode('utf-8')

  def decrypt_token(encrypted_token: str) -> dict:
      """Decrypt token using KMS."""
      kms_client = kms.KeyManagementServiceClient()

      # Decode base64
      ciphertext = base64.b64decode(encrypted_token.encode('utf-8'))

      # Decrypt with KMS
      decrypt_response = kms_client.decrypt(
          request={'name': KMS_KEY_NAME, 'ciphertext': ciphertext}
      )

      # Parse JSON
      return json.loads(decrypt_response.plaintext.decode('utf-8'))
  ```
- [ ] Verify tests pass (mock KMS in tests)
- [ ] Commit: "feat: add token encryption with GCP KMS"

**Note**: Requires KMS key created via Terraform (add to infra in next step)

---

### Step 4: Update Terraform for KMS

**File**: `infra/modules/kms/main.tf` (new module)

- [ ] Create KMS module for key management:
  ```hcl
  resource "google_kms_key_ring" "key_ring" {
    name     = "${var.project_name}-keys"
    location = var.region
  }

  resource "google_kms_crypto_key" "token_encryption" {
    name            = "token-encryption"
    key_ring        = google_kms_key_ring.key_ring.id
    rotation_period = "7776000s"  # 90 days

    lifecycle {
      prevent_destroy = true
    }
  }

  # IAM binding for Cloud Run service account
  resource "google_kms_crypto_key_iam_member" "cloud_run_encrypt_decrypt" {
    crypto_key_id = google_kms_crypto_key.token_encryption.id
    role          = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
    member        = "serviceAccount:${var.cloud_run_service_account}"
  }
  ```

- [ ] Update `infra/environments/dev/main.tf`:
  ```hcl
  module "kms" {
    source = "../../modules/kms"

    project_id   = var.project_id
    project_name = "selflytics"
    region       = var.region
    cloud_run_service_account = module.cloud_run.service_account_email
  }
  ```

- [ ] Apply Terraform: `terraform -chdir=infra/environments/dev apply`
- [ ] Verify KMS key created in GCP Console
- [ ] Commit: "infra: add KMS key for token encryption"

---

### Step 5: GarminClient Service

**File**: `backend/app/services/garmin_client.py`

- [ ] Write tests first: `backend/tests/unit/test_garmin_client.py`
  - Test authenticate (mocked garth)
  - Test get_activities (mocked API response)
  - Test get_daily_metrics (mocked)
  - Test token save/load
  - Test error handling (rate limits, invalid credentials)
- [ ] Adapt GarminClient from garmin_agents:
  ```python
  """Garmin Connect client (async wrapper around garth)."""
  import garth
  from datetime import date, timedelta
  from typing import Optional
  from app.models.garmin_data import GarminActivity, DailyMetrics, HealthSnapshot
  from app.models.garmin_token import GarminToken, GarminTokenDecrypted
  from app.utils.encryption import encrypt_token, decrypt_token
  from app.db.firestore_client import get_firestore_client
  import logging

  logger = logging.getLogger(__name__)

  class GarminClient:
      """Async Garmin Connect client."""

      def __init__(self, user_id: str):
          self.user_id = user_id
          self.db = get_firestore_client()
          self.tokens_collection = self.db.collection("garmin_tokens")

      async def authenticate(self, username: str, password: str) -> bool:
          """
          Authenticate with Garmin Connect (supports MFA).

          Returns True if successful, False otherwise.
          MFA prompts handled interactively by garth.
          """
          try:
              # garth login (may prompt for MFA)
              garth.login(username, password)

              # Save tokens
              await self._save_tokens()

              logger.info(f"Garmin authentication successful for user {self.user_id}")
              return True

          except Exception as e:
              logger.error(f"Garmin authentication failed: {e}")
              return False

      async def load_tokens(self) -> bool:
          """Load saved tokens from Firestore."""
          try:
              doc = self.tokens_collection.document(self.user_id).get()
              if not doc.exists:
                  return False

              token_data = GarminToken(**doc.to_dict())

              # Decrypt tokens
              oauth1 = decrypt_token(token_data.oauth1_token_encrypted)
              oauth2 = decrypt_token(token_data.oauth2_token_encrypted)

              # Set garth tokens
              garth.client.oauth1_token = oauth1
              garth.client.oauth2_token = oauth2

              return True

          except Exception as e:
              logger.error(f"Failed to load tokens: {e}")
              return False

      async def _save_tokens(self):
          """Save garth tokens to Firestore (encrypted)."""
          from datetime import datetime

          # Encrypt tokens
          oauth1_encrypted = encrypt_token(garth.client.oauth1_token)
          oauth2_encrypted = encrypt_token(garth.client.oauth2_token)

          # Create token document
          token = GarminToken(
              user_id=self.user_id,
              oauth1_token_encrypted=oauth1_encrypted,
              oauth2_token_encrypted=oauth2_encrypted,
              token_expiry=None,  # garth handles expiry internally
              last_sync=datetime.utcnow(),
              mfa_enabled=False,  # Can detect from auth flow
              created_at=datetime.utcnow(),
              updated_at=datetime.utcnow()
          )

          # Save to Firestore
          self.tokens_collection.document(self.user_id).set(token.dict())

      async def get_activities(
          self,
          start_date: date,
          end_date: date,
          activity_type: Optional[str] = None
      ) -> list[GarminActivity]:
          """Fetch activities in date range."""
          # Ensure authenticated
          if not await self.load_tokens():
              raise Exception("Not authenticated - user must link Garmin account")

          activities = []
          current_date = start_date

          while current_date <= end_date:
              try:
                  # garth API call
                  day_activities = garth.activities(current_date.isoformat())

                  # Parse and validate
                  for activity_data in day_activities:
                      activity = GarminActivity(**activity_data)

                      # Filter by type if specified
                      if activity_type is None or activity.activity_type == activity_type:
                          activities.append(activity)

              except Exception as e:
                  logger.warning(f"Failed to fetch activities for {current_date}: {e}")

              current_date += timedelta(days=1)

          return activities

      async def get_daily_metrics(self, target_date: date) -> DailyMetrics:
          """Fetch daily summary metrics."""
          if not await self.load_tokens():
              raise Exception("Not authenticated")

          # garth API call
          summary = garth.daily_summary(target_date.isoformat())

          # Parse to model
          return DailyMetrics(
              date=target_date,
              steps=summary.get("steps"),
              distance_meters=summary.get("distanceMeters"),
              active_calories=summary.get("activeCalories"),
              resting_heart_rate=summary.get("restingHeartRate"),
              max_heart_rate=summary.get("maxHeartRate"),
              avg_stress_level=summary.get("avgStressLevel"),
              sleep_seconds=summary.get("sleepSeconds")
          )

      async def get_health_snapshot(self) -> HealthSnapshot:
          """Fetch latest health snapshot."""
          if not await self.load_tokens():
              raise Exception("Not authenticated")

          # garth API call for latest health data
          from datetime import datetime
          health_data = garth.health_snapshot()

          return HealthSnapshot(
              timestamp=datetime.utcnow(),
              heart_rate=health_data.get("heartRate"),
              respiration_rate=health_data.get("respirationRate"),
              stress_level=health_data.get("stressLevel"),
              spo2=health_data.get("spo2")
          )
  ```
- [ ] Verify tests pass
- [ ] Commit: "feat: add GarminClient service with async garth wrapper"

**Implementation Reference**: Adapt from `/Users/bryn/repos/garmin_agents/garmin_client.py`

---

### Step 6: Cache Utilities

**File**: `backend/app/utils/cache.py`

- [ ] Write tests first: `backend/tests/unit/test_cache.py`
  - Test cache key generation
  - Test cache save
  - Test cache load (within TTL)
  - Test cache load (expired)
  - Test cache invalidation
- [ ] Implement cache utilities:
  ```python
  """Caching utilities for Garmin data."""
  from datetime import datetime, timedelta
  from typing import Optional, Any
  from app.db.firestore_client import get_firestore_client
  import json

  class GarminDataCache:
      """Cache for Garmin API responses in Firestore."""

      # TTL values
      TTL_ACTIVITIES = timedelta(hours=24)
      TTL_METRICS = timedelta(hours=6)
      TTL_HEALTH = timedelta(hours=1)

      def __init__(self):
          self.db = get_firestore_client()
          self.collection = self.db.collection("garmin_data")

      def _cache_key(self, user_id: str, data_type: str, **kwargs) -> str:
          """Generate cache key."""
          parts = [user_id, data_type]
          for k, v in sorted(kwargs.items()):
              parts.append(f"{k}:{v}")
          return ":".join(parts)

      async def get(
          self,
          user_id: str,
          data_type: str,
          **kwargs
      ) -> Optional[Any]:
          """Get cached data if available and not expired."""
          cache_key = self._cache_key(user_id, data_type, **kwargs)

          doc = self.collection.document(cache_key).get()
          if not doc.exists:
              return None

          cached = doc.to_dict()

          # Check expiry
          expires_at = cached.get("expires_at")
          if expires_at and datetime.utcnow() > expires_at:
              # Expired - delete and return None
              self.collection.document(cache_key).delete()
              return None

          return cached.get("data")

      async def set(
          self,
          user_id: str,
          data_type: str,
          data: Any,
          ttl: Optional[timedelta] = None,
          **kwargs
      ):
          """Cache data with TTL."""
          cache_key = self._cache_key(user_id, data_type, **kwargs)

          # Determine TTL
          if ttl is None:
              if data_type == "activities":
                  ttl = self.TTL_ACTIVITIES
              elif data_type == "daily_metrics":
                  ttl = self.TTL_METRICS
              elif data_type == "health_snapshot":
                  ttl = self.TTL_HEALTH
              else:
                  ttl = timedelta(hours=1)

          expires_at = datetime.utcnow() + ttl
          cached_at = datetime.utcnow()

          # Save to Firestore
          self.collection.document(cache_key).set({
              "user_id": user_id,
              "data_type": data_type,
              "data": data if isinstance(data, dict) else json.loads(data.json()),
              "cached_at": cached_at,
              "expires_at": expires_at,
              "cache_key": cache_key
          })

      async def invalidate(self, user_id: str, data_type: Optional[str] = None):
          """Invalidate cached data for user."""
          if data_type:
              # Invalidate specific type
              query = self.collection.where("user_id", "==", user_id).where("data_type", "==", data_type)
          else:
              # Invalidate all
              query = self.collection.where("user_id", "==", user_id)

          docs = query.stream()
          for doc in docs:
              doc.reference.delete()
  ```
- [ ] Verify tests pass
- [ ] Commit: "feat: add caching utilities for Garmin data"

---

### Step 7: Garmin Service (OAuth Flow)

**File**: `backend/app/services/garmin_service.py`

- [ ] Write tests first: `backend/tests/integration/test_garmin_oauth.py`
  - Test initiate OAuth flow
  - Test handle OAuth callback
  - Test link Garmin account to user
  - Test sync data after linking
- [ ] Implement GarminService:
  ```python
  """Garmin service for OAuth and data management."""
  from app.services.garmin_client import GarminClient
  from app.utils.cache import GarminDataCache
  from app.services.user_service import UserService
  from datetime import date, timedelta
  import logging

  logger = logging.getLogger(__name__)

  class GarminService:
      """High-level Garmin integration service."""

      def __init__(self, user_id: str):
          self.user_id = user_id
          self.client = GarminClient(user_id)
          self.cache = GarminDataCache()
          self.user_service = UserService()

      async def link_account(self, username: str, password: str) -> bool:
          """
          Link Garmin account to user.

          Returns True if successful, False otherwise.
          """
          # Authenticate
          success = await self.client.authenticate(username, password)

          if success:
              # Update user record
              await self.user_service.update_garmin_status(
                  user_id=self.user_id,
                  linked=True
              )

              # Initial data sync
              await self.sync_recent_data()

          return success

      async def sync_recent_data(self):
          """Sync last 30 days of activities and metrics."""
          end_date = date.today()
          start_date = end_date - timedelta(days=30)

          # Fetch activities
          activities = await self.client.get_activities(start_date, end_date)

          # Cache activities
          await self.cache.set(
              user_id=self.user_id,
              data_type="activities",
              data=[activity.dict() for activity in activities],
              date_range=f"{start_date}:{end_date}"
          )

          logger.info(f"Synced {len(activities)} activities for user {self.user_id}")

      async def get_activities_cached(
          self,
          start_date: date,
          end_date: date
      ) -> list:
          """Get activities with caching."""
          date_range = f"{start_date}:{end_date}"

          # Check cache
          cached = await self.cache.get(
              user_id=self.user_id,
              data_type="activities",
              date_range=date_range
          )

          if cached:
              logger.debug(f"Cache hit for activities {date_range}")
              return cached

          # Fetch from API
          activities = await self.client.get_activities(start_date, end_date)

          # Cache results
          await self.cache.set(
              user_id=self.user_id,
              data_type="activities",
              data=[activity.dict() for activity in activities],
              date_range=date_range
          )

          return [activity.dict() for activity in activities]
  ```
- [ ] Verify tests pass
- [ ] Commit: "feat: add GarminService for OAuth and data sync"

---

### Step 8: Garmin Routes

**File**: `backend/app/routes/garmin.py`

- [ ] Write tests first: `backend/tests/integration/test_garmin_routes.py`
  - Test GET /garmin/link (shows link form)
  - Test POST /garmin/link (initiates OAuth)
  - Test GET /garmin/callback (handles OAuth callback)
  - Test POST /garmin/sync (triggers data sync)
  - Test GET /garmin/status (returns link status)
- [ ] Implement Garmin routes:
  ```python
  """Garmin integration routes."""
  from fastapi import APIRouter, Depends, HTTPException, Request, status
  from fastapi.responses import HTMLResponse, RedirectResponse
  from app.auth.dependencies import get_current_user
  from app.models.user import UserResponse
  from app.services.garmin_service import GarminService
  from pydantic import BaseModel

  router = APIRouter(prefix="/garmin", tags=["garmin"])

  class GarminLinkRequest(BaseModel):
      username: str
      password: str

  @router.get("/link", response_class=HTMLResponse)
  async def garmin_link_page(
      request: Request,
      current_user: UserResponse = Depends(get_current_user)
  ):
      """Display Garmin account linking form."""
      # Render template with current link status
      return templates.TemplateResponse(
          request=request,
          name="settings_garmin.html",
          context={"user": current_user}
      )

  @router.post("/link")
  async def link_garmin_account(
      link_request: GarminLinkRequest,
      current_user: UserResponse = Depends(get_current_user)
  ):
      """Link Garmin account to user."""
      service = GarminService(current_user.user_id)

      success = await service.link_account(
          username=link_request.username,
          password=link_request.password
      )

      if not success:
          raise HTTPException(
              status_code=status.HTTP_400_BAD_REQUEST,
              detail="Failed to link Garmin account. Check credentials."
          )

      return {"message": "Garmin account linked successfully"}

  @router.post("/sync")
  async def sync_garmin_data(
      current_user: UserResponse = Depends(get_current_user)
  ):
      """Manually trigger Garmin data sync."""
      service = GarminService(current_user.user_id)

      try:
          await service.sync_recent_data()
          return {"message": "Sync completed successfully"}
      except Exception as e:
          raise HTTPException(
              status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
              detail=f"Sync failed: {str(e)}"
          )

  @router.get("/status")
  async def garmin_status(
      current_user: UserResponse = Depends(get_current_user)
  ):
      """Get Garmin account link status."""
      return {
          "linked": current_user.garmin_linked,
          "user_id": current_user.user_id
      }
  ```
- [ ] Update `backend/app/main.py` to include router:
  ```python
  from app.routes import garmin
  app.include_router(garmin.router)
  ```
- [ ] Verify tests pass
- [ ] Commit: "feat: add Garmin OAuth routes"

---

### Step 9: Settings Page Template

**File**: `backend/app/templates/settings_garmin.html`

- [ ] Create Garmin settings template:
  ```html
  {% extends "base.html" %}

  {% block content %}
  <div class="max-w-2xl mx-auto py-8">
      <h1 class="text-3xl font-bold mb-6">Garmin Account Settings</h1>

      {% if user.garmin_linked %}
      <!-- Account linked state -->
      <div class="bg-green-50 border border-green-200 rounded-lg p-6 mb-6">
          <p class="text-green-800 font-semibold">✓ Garmin account linked</p>
          <p class="text-sm text-gray-600 mt-2">Your Garmin data is being synchronized automatically.</p>

          <button
              hx-post="/garmin/sync"
              hx-swap="outerHTML"
              class="mt-4 bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
          >
              Sync Now
          </button>
      </div>
      {% else %}
      <!-- Link account form -->
      <div class="bg-white border rounded-lg p-6">
          <h2 class="text-xl font-semibold mb-4">Link Your Garmin Account</h2>
          <p class="text-gray-600 mb-6">
              Connect your Garmin account to enable AI-powered analysis of your fitness data.
          </p>

          <form
              hx-post="/garmin/link"
              hx-swap="outerHTML"
              x-data="{ loading: false }"
              @submit="loading = true"
          >
              <div class="mb-4">
                  <label for="username" class="block text-sm font-medium text-gray-700">
                      Garmin Email
                  </label>
                  <input
                      type="email"
                      id="username"
                      name="username"
                      required
                      class="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
                  >
              </div>

              <div class="mb-6">
                  <label for="password" class="block text-sm font-medium text-gray-700">
                      Garmin Password
                  </label>
                  <input
                      type="password"
                      id="password"
                      name="password"
                      required
                      class="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
                  >
              </div>

              <button
                  type="submit"
                  :disabled="loading"
                  class="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700 disabled:opacity-50"
              >
                  <span x-show="!loading">Link Account</span>
                  <span x-show="loading">Linking...</span>
              </button>
          </form>

          <p class="text-xs text-gray-500 mt-4">
              Your credentials are encrypted and stored securely. We never share your data with third parties.
          </p>
      </div>
      {% endif %}
  </div>
  {% endblock %}
  ```
- [ ] Commit: "feat: add Garmin settings page template"

---

### Step 10: Integration Tests

**File**: `backend/tests/integration/test_garmin_data_fetch.py`

- [ ] Write comprehensive data fetching tests:
  - Test fetch activities with mocked API
  - Test cache hit scenario
  - Test cache miss scenario
  - Test data sync workflow
- [ ] Use mocked garth responses
- [ ] Verify caching behavior
- [ ] Commit: "test: add integration tests for Garmin data fetching"

---

### Final Steps

- [ ] Run full test suite: `uv run pytest backend/tests/ -v --cov=app`
- [ ] Verify 80%+ coverage on new code
- [ ] Run quality checks:
  - `uv run ruff check .`
  - `uv run ruff format .`
- [ ] Manual testing:
  - Start server: `uv run --directory backend uvicorn app.main:app --reload`
  - Visit settings: http://localhost:8000/garmin/link
  - Test account linking (with real Garmin credentials)
  - Verify MFA flow (if account has MFA)
  - Test data sync: POST to /garmin/sync
  - Check Firestore: verify encrypted tokens stored
  - Check cache: verify activities cached
- [ ] Terraform updates:
  - Apply KMS changes: `terraform -chdir=infra/environments/dev apply`
  - Verify KMS key created
- [ ] Final commit: "feat: complete Phase 2 - Garmin Integration"
- [ ] Update this plan: mark all steps ✅ DONE
- [ ] Update `docs/project-setup/ROADMAP.md`: Phase 2 status → ✅ DONE
- [ ] Create PR: `feat/phase-2-garmin` → `main`

---

## Success Criteria

- ✅ User can link Garmin account via settings page
- ✅ OAuth flow completes successfully (including MFA)
- ✅ Activities from last 30 days cached in Firestore
- ✅ Cache hit/miss logic works correctly
- ✅ Tokens encrypted with KMS before storage
- ✅ Tokens decrypt successfully for API calls
- ✅ Manual sync triggers data fetch
- ✅ Error handling for invalid credentials
- ✅ 80%+ test coverage achieved
- ✅ All integration tests pass

---

## Notes

### Design Decisions

1. **KMS Encryption**: Using GCP KMS for token encryption instead of application-level encryption. More secure, managed key rotation.

2. **Cache in Firestore**: Using Firestore for cache (not Redis) to minimize infrastructure. TTL enforced at read time with cleanup.

3. **MFA Handling**: garth library handles MFA interactively. For automated systems (future), will need token refresh logic.

4. **OAuth vs Direct Login**: Phase 2 uses direct login (username/password) for simplicity. Future phases may add OAuth redirect flow.

5. **Sync Strategy**: Manual sync only in Phase 2. Phase 3+ can add background jobs for automatic sync.

### Reference Implementations

**From Garmin Agents**:
- `garmin_agents/garmin_client.py` - Core client logic
- `garmin_agents/tools/` - Tool definitions (adapt to Pydantic-AI in Phase 3)
- MFA flow patterns

**From CliniCraft**:
- Settings page template pattern
- Service layer structure
- Caching utilities

### Common Pitfalls

- **garth async**: garth is synchronous. Wrap in async functions for FastAPI compatibility.
- **Token expiry**: garth handles token refresh internally. Monitor for expired token errors.
- **Rate limits**: Garmin API has rate limits. Caching mitigates this, but add exponential backoff for retries.
- **MFA testing**: Requires manual testing with MFA-enabled account. Cannot fully automate in CI.

### Deferred to Future Phases

- OAuth redirect flow (instead of username/password)
- Background sync jobs (automatic data refresh)
- Token refresh on expiry (garth handles this, but add monitoring)
- Multiple wearable integrations (Fitbit, Apple Health)

---

## Dependencies for Next Phase

**Phase 3** (Chat + AI Agent) will need:
- ✅ Garmin data available via GarminService
- ✅ Caching layer working (fast data access)
- ✅ User Garmin link status in profile
- ✅ Pydantic models for Garmin data (for tool responses)

With Phase 2 complete, Phase 3 can build Pydantic-AI tools that query real Garmin data with intelligent caching.

---

*Last Updated: 2025-11-11*
*Status: ⬜ TODO*
