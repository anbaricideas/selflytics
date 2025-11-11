# Phase 1: Infrastructure Foundation

**Branch**: `feat/phase-1-infrastructure`
**Status**: ⬜ TODO

---

## Goal

Establish production-ready infrastructure and authentication foundation for Selflytics. This phase creates the complete project structure (following CliniCraft patterns), deploys core GCP resources via Terraform, and implements user authentication with JWT tokens.

**Key Deliverables**:
- Complete monorepo structure (all folders from day one)
- Terraform infrastructure deployed to dev environment
- User authentication (register, login, JWT tokens)
- Frontend templates (base, login, register, dashboard)
- Telemetry workspace package with Cloud Logging
- GitHub Actions CI/CD pipeline
- 80%+ test coverage for auth flows

---

## Prerequisites

- ✅ Spike completed successfully (decision to proceed)
- ✅ GCP project exists: selflytics-infra (174666459313)
- ✅ GitHub repository: https://github.com/anbaricideas/selflytics
- ✅ Local development environment configured (uv, Python 3.12+, Terraform)

---

## Deliverables

### Project Structure (Copy from CliniCraft)

- ✅ Complete folder structure created (see Appendix A in specification)
- ✅ `backend/` - FastAPI application
- ✅ `backend/packages/telemetry/` - Workspace package
- ✅ `infra/` - Terraform modules and environments
- ✅ `static/` - Frontend assets (CSS, JS, images)
- ✅ `scripts/` - Utility scripts
- ✅ `.github/workflows/` - CI/CD pipelines
- ✅ Configuration files (`.env.example`, `pyproject.toml`, etc.)

### Infrastructure (Terraform)

- ✅ `infra/modules/cloud_run/` - Cloud Run service module
- ✅ `infra/modules/cloud_run_preview/` - Preview environment module
- ✅ `infra/modules/firestore/` - Firestore database module
- ✅ `infra/modules/secrets/` - Secret Manager module
- ✅ `infra/modules/storage/` - GCS bucket module
- ✅ `infra/environments/dev/` - Dev environment configuration
- ✅ Deployed to GCP: Cloud Run, Firestore, Secret Manager, Cloud Logging

### Authentication (Backend)

- ✅ `backend/app/auth/jwt.py` - JWT token handling
- ✅ `backend/app/auth/password.py` - Password hashing (bcrypt)
- ✅ `backend/app/auth/dependencies.py` - FastAPI dependencies
- ✅ `backend/app/auth/schemas.py` - Pydantic models
- ✅ `backend/app/services/user_service.py` - User CRUD operations
- ✅ `backend/app/routes/auth.py` - Auth endpoints
- ✅ `backend/app/models/user.py` - User Pydantic model

### Frontend Templates

- ✅ `backend/app/templates/base.html` - Base template with nav
- ✅ `backend/app/templates/login.html` - Login form
- ✅ `backend/app/templates/register.html` - Registration form
- ✅ `backend/app/templates/dashboard.html` - User dashboard
- ✅ TailwindCSS integration (CDN)
- ✅ Alpine.js integration (CDN)
- ✅ HTMX integration (CDN)

### Telemetry Package

- ✅ `backend/packages/telemetry/` - Workspace package (copy from CliniCraft)
- ✅ Cloud Logging exporter configured
- ✅ OpenTelemetry integration
- ✅ Middleware for request tracing

### CI/CD Pipeline

- ✅ `.github/workflows/ci.yml` - Quality gates (lint, test, security, terraform)
- ✅ `.github/workflows/cd.yml` - Deployment to dev
- ✅ `.github/workflows/preview.yml` - Preview deployments
- ✅ `.github/workflows/preview-cleanup.yml` - Preview cleanup
- ✅ Workload Identity Federation configured

### Tests

- ✅ `backend/tests/unit/test_jwt.py` - JWT token tests
- ✅ `backend/tests/unit/test_password.py` - Password hashing tests
- ✅ `backend/tests/unit/test_user_service.py` - User service tests
- ✅ `backend/tests/integration/test_auth_flow.py` - Login/register flow
- ✅ `backend/tests/integration/test_protected_routes.py` - Auth middleware
- ✅ 80%+ coverage on new code

---

## Implementation Steps

### Setup

- [x] Create branch `feat/phase-1-infrastructure`
- [x] Review CliniCraft structure: `/Users/bryn/repos/clinicraft/`
- [x] Prepare to copy folders and configuration files

---

### Step 1: Create Complete Project Structure

**Goal**: Establish all folders from day one (CliniCraft pattern)

- [ ] Create root-level structure:
  ```
  backend/
  infra/
  static/
  scripts/
  docs/
  .github/
  ```

- [ ] Create backend application structure:
  ```
  backend/app/
  backend/app/auth/
  backend/app/db/
  backend/app/middleware/
  backend/app/models/
  backend/app/routes/
  backend/app/services/
  backend/app/templates/
  backend/app/templates/partials/
  backend/app/prompts/
  backend/app/utils/
  ```

- [ ] Create backend packages structure:
  ```
  backend/packages/telemetry/
  backend/packages/telemetry/src/selflytics_telemetry/
  backend/packages/telemetry/src/selflytics_telemetry/config/
  backend/packages/telemetry/tests/
  ```

- [ ] Create test structure:
  ```
  backend/tests/unit/
  backend/tests/unit/services/
  backend/tests/unit/models/
  backend/tests/unit/utils/
  backend/tests/integration/
  backend/tests/integration/routers/
  backend/tests/e2e/
  ```

- [ ] Create infrastructure structure:
  ```
  infra/modules/cloud_run/
  infra/modules/cloud_run_preview/
  infra/modules/firestore/
  infra/modules/secrets/
  infra/modules/storage/
  infra/environments/dev/
  infra/scripts/
  infra/scripts/commands/
  infra/scripts/lib/
  ```

- [ ] Add `__init__.py` to all Python packages
- [ ] Add placeholder README.md files to key directories
- [ ] Commit: "chore: create complete project structure"

**Implementation Notes**:
- Copy structure from CliniCraft: `/Users/bryn/repos/clinicraft/`
- Ensure all folders exist even if empty
- This enables parallel development in future phases

---

### Step 2: Copy and Adapt Configuration Files

**File**: `backend/pyproject.toml`

- [x] Copy from CliniCraft `backend/pyproject.toml`
- [x] Update project name: `selflytics`
- [x] Update version: `0.1.0`
- [ ] Update dependencies (minimal set for Phase 1):
  ```toml
  dependencies = [
      "fastapi>=0.109.0",
      "uvicorn[standard]>=0.27.0",
      "pydantic>=2.6.0",
      "pydantic-settings>=2.0.0",
      "python-jose[cryptography]>=3.3.0",
      "passlib[bcrypt]>=1.7.4",
      "google-cloud-firestore>=2.14.0",
      "google-cloud-secret-manager>=2.18.0",
      "jinja2>=3.1.3",
      "python-multipart>=0.0.6",
  ]
  ```
- [ ] Keep workspace dependencies for telemetry package:
  ```toml
  [tool.uv.sources]
  selflytics-telemetry = { workspace = true }

  [tool.uv.workspace]
  members = ["packages/*"]
  ```
- [ ] Keep ruff configuration (copy from CliniCraft)
- [ ] Keep pytest configuration (copy from CliniCraft)
- [ ] Commit: "chore: add pyproject.toml with workspace configuration"

**File**: `.pre-commit-config.yaml`

- [x] Copy from CliniCraft (direct copy, no changes)
- [x] Commit: "chore: add pre-commit configuration"

**File**: `.gitignore`

- [x] Copy from CliniCraft
- [x] Add spike-specific ignores:
  ```
  spike/cache/
  spike/.env
  ```
- [ ] Commit: "chore: add gitignore"

**Files**: `.env.example` (root and backend)

- [ ] Create root `.env.example`:
  ```bash
  # GCP Configuration
  GCP_PROJECT_ID=selflytics-infra
  GCP_REGION=australia-southeast1

  # Workload Identity Federation
  WIF_PROVIDER=projects/174666459313/locations/global/workloadIdentityPools/github-pool/providers/github-provider
  WIF_SERVICE_ACCOUNT=github-actions@selflytics-infra.iam.gserviceaccount.com
  ```

- [ ] Create `backend/.env.example`:
  ```bash
  # Application
  ENVIRONMENT=dev
  DEBUG=true

  # Database
  FIRESTORE_DATABASE=(default)

  # Authentication
  JWT_SECRET_KEY=your-secret-key-here-change-in-production
  JWT_ALGORITHM=HS256
  ACCESS_TOKEN_EXPIRE_MINUTES=30

  # Telemetry
  TELEMETRY_BACKEND=cloudlogging
  GCP_PROJECT_ID=selflytics-infra
  ```

- [ ] Commit: "chore: add environment configuration templates"

---

### Step 3: Copy Telemetry Workspace Package

**Goal**: Reuse CliniCraft telemetry package (Cloud Logging integration)

- [x] Copy entire directory: `clinicraft/backend/packages/telemetry/` → `selflytics/backend/packages/telemetry/`
- [x] Update package name in `backend/packages/telemetry/pyproject.toml` to `selflytics-telemetry`
- [x] Keep import name as `telemetry` (simpler, avoid unnecessary complexity)
- [x] Commit: "feat: add telemetry workspace package from CliniCraft"

**Implementation Notes**:
- Direct copy acceptable - telemetry is generic
- Cloud Logging exporter already configured
- Import remains `from telemetry import ...` for simplicity

---

### Step 4: Authentication - Password Hashing

**File**: `backend/app/auth/password.py`

- [x] Write tests first: `backend/tests/unit/test_password.py` (13 comprehensive tests)
- [x] Review tests for quality with test-quality-reviewer agent
- [x] Verify tests fail (no implementation yet)
- [x] Implement password hashing functions using bcrypt directly (not passlib):
  ```python
  """Password hashing utilities using bcrypt."""
  from passlib.context import CryptContext

  pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

  def hash_password(password: str) -> str:
      """Hash password using bcrypt."""
      return pwd_context.hash(password)

  def verify_password(plain_password: str, hashed_password: str) -> bool:
      """Verify password against hash."""
      return pwd_context.verify(plain_password, hashed_password)
  ```
- [ ] Verify tests pass
- [ ] Commit: "feat: add password hashing with bcrypt"

**Implementation Reference**: `clinicraft/backend/app/auth/password.py` (direct copy)

---

### Step 5: Authentication - JWT Tokens

**File**: `backend/app/auth/jwt.py`

- [x] Write tests first: `backend/tests/unit/test_jwt.py` (10 comprehensive tests)
- [x] Create config module: `backend/app/config.py` (Pydantic Settings)
- [x] Verify tests fail
- [x] Implement JWT functions:
  ```python
  """JWT token handling."""
  from datetime import datetime, timedelta
  from typing import Optional
  from jose import JWTError, jwt
  from pydantic import BaseModel

  SECRET_KEY = "..."  # From environment
  ALGORITHM = "HS256"
  ACCESS_TOKEN_EXPIRE_MINUTES = 30

  class TokenData(BaseModel):
      user_id: str
      email: str

  def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
      """Create JWT access token."""
      to_encode = data.copy()
      expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
      to_encode.update({"exp": expire})
      return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

  def verify_token(token: str) -> TokenData:
      """Decode and verify JWT token."""
      try:
          payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
          user_id: str = payload.get("sub")
          email: str = payload.get("email")
          if user_id is None or email is None:
              raise ValueError("Invalid token payload")
          return TokenData(user_id=user_id, email=email)
      except JWTError:
          raise ValueError("Invalid token")
  ```
- [ ] Verify tests pass
- [ ] Commit: "feat: add JWT token creation and verification"

**Implementation Reference**: `clinicraft/backend/app/auth/jwt.py`

---

### Step 6: User Model and Service

**File**: `backend/app/models/user.py`

- [ ] Write tests first: `backend/tests/unit/test_user_model.py`
  - Test User model validation
  - Test email format validation
  - Test password requirements
- [ ] Implement User Pydantic model:
  ```python
  """User data models."""
  from pydantic import BaseModel, EmailStr, Field
  from datetime import datetime
  from typing import Optional

  class UserProfile(BaseModel):
      display_name: str
      timezone: str = "Australia/Sydney"
      units: str = "metric"  # or "imperial"

  class User(BaseModel):
      user_id: str
      email: EmailStr
      hashed_password: str
      created_at: datetime
      updated_at: datetime
      profile: UserProfile
      garmin_linked: bool = False
      garmin_link_date: Optional[datetime] = None

  class UserCreate(BaseModel):
      email: EmailStr
      password: str = Field(..., min_length=8)
      display_name: str

  class UserResponse(BaseModel):
      """User data for API responses (no password)."""
      user_id: str
      email: str
      profile: UserProfile
      garmin_linked: bool
  ```
- [ ] Verify tests pass
- [ ] Commit: "feat: add User Pydantic models"

**File**: `backend/app/services/user_service.py`

- [ ] Write tests first: `backend/tests/unit/test_user_service.py`
  - Test create_user (mocked Firestore)
  - Test get_user_by_email
  - Test get_user_by_id
  - Test update_user
  - Test password hashing on creation
- [ ] Implement UserService with Firestore:
  ```python
  """User service for CRUD operations."""
  from app.models.user import User, UserCreate, UserProfile
  from app.auth.password import hash_password
  from app.db.firestore_client import get_firestore_client
  from datetime import datetime
  import uuid

  class UserService:
      def __init__(self):
          self.db = get_firestore_client()
          self.collection = self.db.collection("users")

      async def create_user(self, user_data: UserCreate) -> User:
          """Create new user."""
          user_id = str(uuid.uuid4())
          now = datetime.utcnow()

          user = User(
              user_id=user_id,
              email=user_data.email,
              hashed_password=hash_password(user_data.password),
              created_at=now,
              updated_at=now,
              profile=UserProfile(display_name=user_data.display_name),
              garmin_linked=False
          )

          # Save to Firestore
          self.collection.document(user_id).set(user.dict())
          return user

      async def get_user_by_email(self, email: str) -> User | None:
          """Get user by email."""
          query = self.collection.where("email", "==", email).limit(1)
          results = query.stream()

          for doc in results:
              return User(**doc.to_dict())
          return None

      async def get_user_by_id(self, user_id: str) -> User | None:
          """Get user by ID."""
          doc = self.collection.document(user_id).get()
          if doc.exists:
              return User(**doc.to_dict())
          return None
  ```
- [ ] Verify tests pass
- [ ] Commit: "feat: add UserService with Firestore integration"

**Implementation Reference**: `clinicraft/backend/app/services/user_service.py`

---

### Step 7: Firestore Client

**File**: `backend/app/db/firestore_client.py`

- [ ] Write tests first: `backend/tests/unit/test_firestore_client.py`
  - Test client initialization
  - Test client returns Firestore instance
  - Test error handling for missing credentials
- [ ] Implement Firestore client:
  ```python
  """Firestore database client."""
  from google.cloud import firestore
  from functools import lru_cache

  @lru_cache()
  def get_firestore_client() -> firestore.Client:
      """Get Firestore client (cached)."""
      return firestore.Client()
  ```
- [ ] Verify tests pass (with mocked Firestore)
- [ ] Commit: "feat: add Firestore client"

**Implementation Reference**: `clinicraft/backend/app/db/firestore_client.py`

---

### Step 8: Authentication Routes

**File**: `backend/app/routes/auth.py`

- [ ] Write tests first: `backend/tests/integration/test_auth_flow.py`
  - Test POST /auth/register (success)
  - Test POST /auth/register (duplicate email)
  - Test POST /auth/login (success)
  - Test POST /auth/login (invalid credentials)
  - Test GET /auth/me (with valid token)
  - Test GET /auth/me (with invalid token)
- [ ] Implement auth routes:
  ```python
  """Authentication routes."""
  from fastapi import APIRouter, Depends, HTTPException, status
  from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
  from app.models.user import UserCreate, UserResponse
  from app.services.user_service import UserService
  from app.auth.jwt import create_access_token, verify_token
  from app.auth.password import verify_password

  router = APIRouter(prefix="/auth", tags=["authentication"])
  oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

  @router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
  async def register(user_data: UserCreate):
      """Register new user."""
      user_service = UserService()

      # Check if email exists
      existing_user = await user_service.get_user_by_email(user_data.email)
      if existing_user:
          raise HTTPException(
              status_code=status.HTTP_400_BAD_REQUEST,
              detail="Email already registered"
          )

      # Create user
      user = await user_service.create_user(user_data)

      return UserResponse(
          user_id=user.user_id,
          email=user.email,
          profile=user.profile,
          garmin_linked=user.garmin_linked
      )

  @router.post("/login")
  async def login(form_data: OAuth2PasswordRequestForm = Depends()):
      """Login user and return access token."""
      user_service = UserService()

      # Get user by email
      user = await user_service.get_user_by_email(form_data.username)
      if not user or not verify_password(form_data.password, user.hashed_password):
          raise HTTPException(
              status_code=status.HTTP_401_UNAUTHORIZED,
              detail="Incorrect email or password",
              headers={"WWW-Authenticate": "Bearer"},
          )

      # Create access token
      access_token = create_access_token(data={"sub": user.user_id, "email": user.email})

      return {
          "access_token": access_token,
          "token_type": "bearer"
      }

  async def get_current_user(token: str = Depends(oauth2_scheme)) -> UserResponse:
      """Get current user from JWT token."""
      try:
          token_data = verify_token(token)
      except ValueError:
          raise HTTPException(
              status_code=status.HTTP_401_UNAUTHORIZED,
              detail="Could not validate credentials",
              headers={"WWW-Authenticate": "Bearer"},
          )

      user_service = UserService()
      user = await user_service.get_user_by_id(token_data.user_id)

      if user is None:
          raise HTTPException(
              status_code=status.HTTP_401_UNAUTHORIZED,
              detail="User not found"
          )

      return UserResponse(
          user_id=user.user_id,
          email=user.email,
          profile=user.profile,
          garmin_linked=user.garmin_linked
      )

  @router.get("/me", response_model=UserResponse)
  async def get_me(current_user: UserResponse = Depends(get_current_user)):
      """Get current user info."""
      return current_user
  ```
- [ ] Verify tests pass
- [ ] Commit: "feat: add authentication routes (register, login, me)"

**Implementation Reference**: `clinicraft/backend/app/routes/auth.py`

---

### Step 9: Frontend Templates

**File**: `backend/app/templates/base.html`

- [ ] Copy from CliniCraft `backend/app/templates/base.html`
- [ ] Update branding: "Selflytics" instead of "CliniCraft"
- [ ] Keep TailwindCSS CDN
- [ ] Keep Alpine.js CDN
- [ ] Keep HTMX CDN
- [ ] Update navigation links:
  - Home, Dashboard, Settings, Logout
- [ ] Commit: "feat: add base template with TailwindCSS and Alpine.js"

**File**: `backend/app/templates/login.html`

- [ ] Copy from CliniCraft `backend/app/templates/login.html`
- [ ] Update form action: `POST /auth/login`
- [ ] Keep HTMX for async form submission
- [ ] Keep Alpine.js for loading states
- [ ] Commit: "feat: add login template"

**File**: `backend/app/templates/register.html`

- [ ] Copy from CliniCraft `backend/app/templates/register.html`
- [ ] Update form action: `POST /auth/register`
- [ ] Add display_name field
- [ ] Keep HTMX and Alpine.js
- [ ] Commit: "feat: add registration template"

**File**: `backend/app/templates/dashboard.html`

- [ ] Create minimal dashboard:
  - Welcome message with user name
  - Placeholder for recent activities (Phase 2)
  - Link to Garmin account setup (Phase 2)
  - Link to chat interface (Phase 3)
- [ ] Commit: "feat: add dashboard template"

**Implementation Reference**: CliniCraft templates directory

---

### Step 10: Main Application and Configuration

**File**: `backend/app/config.py`

- [ ] Copy from CliniCraft `backend/app/config.py`
- [ ] Update settings for Selflytics:
  ```python
  """Application configuration."""
  from pydantic_settings import BaseSettings

  class Settings(BaseSettings):
      # Application
      app_name: str = "Selflytics"
      environment: str = "dev"
      debug: bool = False

      # Database
      firestore_database: str = "(default)"

      # Authentication
      jwt_secret_key: str
      jwt_algorithm: str = "HS256"
      access_token_expire_minutes: int = 30

      # Telemetry
      telemetry_backend: str = "cloudlogging"
      gcp_project_id: str = "selflytics-infra"

      class Config:
          env_file = ".env"

  settings = Settings()
  ```
- [ ] Commit: "feat: add application configuration with Pydantic Settings"

**File**: `backend/app/main.py`

- [ ] Copy from CliniCraft `backend/app/main.py`
- [ ] Update app metadata
- [ ] Include auth router
- [ ] Include telemetry middleware
- [ ] Add CORS middleware (development only)
- [ ] Example:
  ```python
  """FastAPI application entry point."""
  from fastapi import FastAPI
  from fastapi.middleware.cors import CORSMiddleware
  from app.routes import auth
  from app.config import settings
  from app.middleware.telemetry import TelemetryMiddleware

  app = FastAPI(
      title="Selflytics API",
      description="AI-powered analysis for quantified self data",
      version="0.1.0"
  )

  # CORS (development only)
  if settings.debug:
      app.add_middleware(
          CORSMiddleware,
          allow_origins=["*"],
          allow_credentials=True,
          allow_methods=["*"],
          allow_headers=["*"],
      )

  # Telemetry
  app.add_middleware(TelemetryMiddleware)

  # Routes
  app.include_router(auth.router)

  @app.get("/health")
  async def health_check():
      return {"status": "healthy", "service": "selflytics"}
  ```
- [ ] Commit: "feat: add main FastAPI application"

**File**: `backend/app/telemetry_config.py`

- [ ] Copy from CliniCraft `backend/app/telemetry_config.py`
- [ ] Update for Selflytics (minimal changes needed)
- [ ] Commit: "feat: add telemetry configuration"

**File**: `backend/app/middleware/telemetry.py`

- [ ] Copy from CliniCraft `backend/app/middleware/telemetry.py`
- [ ] Direct copy acceptable
- [ ] Commit: "feat: add telemetry middleware"

---

### Step 11: Terraform Infrastructure

**Goal**: Deploy Cloud Run, Firestore, Secret Manager, GCS

- [ ] Copy Terraform modules from CliniCraft:
  - `infra/modules/cloud_run/` → Direct copy
  - `infra/modules/cloud_run_preview/` → Direct copy
  - `infra/modules/firestore/` → Direct copy
  - `infra/modules/secrets/` → Direct copy
  - `infra/modules/storage/` → Direct copy (for future visualization storage)

- [ ] Create `infra/environments/dev/main.tf`:
  ```hcl
  terraform {
    required_version = ">= 1.5.0"
    required_providers {
      google = {
        source  = "hashicorp/google"
        version = "~> 5.0"
      }
    }
  }

  provider "google" {
    project = var.project_id
    region  = var.region
  }

  # Cloud Run
  module "cloud_run" {
    source = "../../modules/cloud_run"

    project_id   = var.project_id
    region       = var.region
    service_name = "selflytics-dev"
    image        = var.image
    env_vars = {
      ENVIRONMENT             = "dev"
      FIRESTORE_DATABASE      = "(default)"
      TELEMETRY_BACKEND       = "cloudlogging"
      GCP_PROJECT_ID          = var.project_id
    }
  }

  # Firestore
  module "firestore" {
    source = "../../modules/firestore"

    project_id = var.project_id
    region     = var.region
  }

  # Secret Manager
  module "secrets" {
    source = "../../modules/secrets"

    project_id = var.project_id
    secrets = {
      jwt-secret-key         = "JWT secret for token signing"
      openai-api-key         = "OpenAI API key"
      garmin-client-secret   = "Garmin OAuth client secret"
    }
  }

  # Storage for visualizations (Phase 4)
  module "storage" {
    source = "../../modules/storage"

    project_id  = var.project_id
    bucket_name = "selflytics-viz"
    region      = var.region
  }
  ```

- [ ] Create `infra/environments/dev/variables.tf`:
  ```hcl
  variable "project_id" {
    description = "GCP project ID"
    type        = string
    default     = "selflytics-infra"
  }

  variable "region" {
    description = "GCP region"
    type        = string
    default     = "australia-southeast1"
  }

  variable "image" {
    description = "Container image"
    type        = string
    default     = "australia-southeast1-docker.pkg.dev/selflytics-infra/selflytics/backend:latest"
  }
  ```

- [ ] Create `infra/environments/dev/backend.tf`:
  ```hcl
  terraform {
    backend "gcs" {
      bucket = "selflytics-infra-terraform-state"
      prefix = "environments/dev"
    }
  }
  ```

- [ ] Initialize Terraform: `terraform -chdir=infra/environments/dev init`
- [ ] Validate configuration: `terraform -chdir=infra/environments/dev validate`
- [ ] Commit: "feat: add Terraform infrastructure configuration"

**Implementation Reference**: CliniCraft infra directory (copy structure)

---

### Step 12: CI/CD Pipeline

**File**: `.github/workflows/ci.yml`

- [ ] Copy from CliniCraft `.github/workflows/ci.yml`
- [ ] Update workflow name: "Selflytics CI"
- [ ] Update paths to watch
- [ ] Keep jobs: lint, test, security, terraform-validate
- [ ] Commit: "ci: add CI pipeline"

**File**: `.github/workflows/cd.yml`

- [ ] Copy from CliniCraft `.github/workflows/cd.yml`
- [ ] Update for Selflytics project
- [ ] Update GCP project ID: selflytics-infra
- [ ] Update image registry path
- [ ] Commit: "ci: add CD pipeline for dev deployment"

**File**: `.github/workflows/preview.yml`

- [ ] Copy from CliniCraft `.github/workflows/preview.yml`
- [ ] Update for Selflytics project
- [ ] Commit: "ci: add preview deployment workflow"

**File**: `.github/workflows/preview-cleanup.yml`

- [ ] Copy from CliniCraft `.github/workflows/preview-cleanup.yml`
- [ ] Update for Selflytics project
- [ ] Commit: "ci: add preview cleanup workflow"

**Implementation Reference**: CliniCraft `.github/workflows/` directory

---

### Step 13: Integration Tests

**File**: `backend/tests/integration/test_auth_flow.py`

- [ ] Write comprehensive auth flow tests:
  - Test full registration flow
  - Test login with registered user
  - Test accessing protected endpoint with token
  - Test token refresh
  - Test logout (token invalidation)
- [ ] Use FastAPI TestClient
- [ ] Mock Firestore for CI
- [ ] Verify 80%+ coverage on auth code
- [ ] Commit: "test: add integration tests for auth flows"

**File**: `backend/tests/integration/test_protected_routes.py`

- [ ] Test route protection:
  - Test /auth/me requires authentication
  - Test invalid token rejected
  - Test expired token rejected
  - Test missing token rejected
- [ ] Commit: "test: add tests for protected routes"

**Implementation Reference**: CliniCraft integration tests

---

### Step 14: Documentation

**File**: `backend/README.md`

- [ ] Write backend-specific documentation:
  - Project structure overview
  - Local development setup
  - Running tests
  - Environment configuration
  - Common commands
- [ ] Commit: "docs: add backend README"

**File**: `README.md` (project root)

- [ ] Write project overview:
  - What is Selflytics
  - Quick start guide
  - Repository structure
  - Development workflow
  - Links to detailed docs
- [ ] Commit: "docs: add project README"

**File**: `.claude/CLAUDE.md` (project-specific)

- [ ] Copy from CliniCraft `.claude/CLAUDE.md`
- [ ] Update for Selflytics specifics:
  - Project context
  - GCP project details
  - Reference project locations
- [ ] Commit: "docs: add Claude Code configuration"

---

### Final Steps

- [ ] Run full test suite: `uv run pytest backend/tests/ -v --cov=app`
- [ ] Verify 80%+ coverage
- [ ] Run quality checks:
  - `uv run ruff check .`
  - `uv run ruff format .`
  - `uv run bandit -c backend/pyproject.toml -r backend/app/ -ll`
- [ ] Manual testing:
  - Start server: `uv run --directory backend uvicorn app.main:app --reload`
  - Test registration: POST to /auth/register
  - Test login: POST to /auth/login
  - Test protected route: GET /auth/me with token
  - Visit login page: http://localhost:8000/login
  - Visit dashboard: http://localhost:8000/dashboard (after login)
- [ ] Terraform plan: `terraform -chdir=infra/environments/dev plan`
- [ ] Deploy to GCP: `terraform -chdir=infra/environments/dev apply`
- [ ] Validate deployment: `./scripts/validate-deployment.sh <deployed-url>`
- [ ] Final commit: "feat: complete Phase 1 - Infrastructure Foundation"
- [ ] Update this plan: mark all steps ✅ DONE
- [ ] Update `docs/project-setup/ROADMAP.md`: Phase 1 status → ✅ DONE
- [ ] Create PR: `feat/phase-1-infrastructure` → `main`

---

## Testing Requirements

### Unit Tests (Target: 60% of test suite)

- [ ] Password hashing (hash, verify, edge cases)
- [ ] JWT token creation and verification
- [ ] User model validation
- [ ] UserService methods (mocked Firestore)
- [ ] Firestore client initialization

### Integration Tests (Target: 30% of test suite)

- [ ] Full registration flow (API)
- [ ] Login flow (API)
- [ ] Protected route access (API)
- [ ] Token validation (API)
- [ ] Error handling (duplicate email, invalid credentials)

### E2E Tests (Target: 10% of test suite)

- [ ] Complete user journey: register → login → access dashboard
- [ ] Frontend form submission (if time permits)

### Coverage Requirements

- [ ] 80%+ coverage on `app/auth/`
- [ ] 80%+ coverage on `app/services/user_service.py`
- [ ] 80%+ coverage on `app/routes/auth.py`

---

## Success Criteria

- ✅ Complete project structure created (all folders from day one)
- ✅ User can register and receive confirmation
- ✅ User can login and receive JWT token
- ✅ User can access dashboard (protected route)
- ✅ JWT token validation works correctly
- ✅ Passwords hashed with bcrypt
- ✅ Firestore stores user data
- ✅ Terraform infrastructure deploys successfully
- ✅ Cloud Run service accessible via URL
- ✅ Cloud Logging telemetry working
- ✅ CI pipeline passes all quality gates
- ✅ 80%+ test coverage achieved
- ✅ Frontend templates render correctly
- ✅ All authentication flows tested and working

---

## Notes

### Design Decisions

1. **Complete Structure from Day One**: Following CliniCraft pattern - all folders created in Phase 1 even if empty. Enables parallel development in future phases.

2. **Direct CliniCraft Copies**: Telemetry package, Terraform modules, CI/CD workflows - proven code, minimal adaptation needed.

3. **Firestore Collections**: Phase 1 creates only `users` collection. Phase 2 adds `garmin_tokens`, Phase 3 adds `conversations`.

4. **JWT in Cookies**: Frontend stores JWT in httpOnly cookies (CliniCraft pattern). More secure than localStorage.

5. **TailwindCSS CDN**: Using CDN (no build step) for simplicity. Matches CliniCraft approach.

### Reference Implementations

**Complete copies from CliniCraft**:
- Telemetry package: `backend/packages/telemetry/`
- Terraform modules: `infra/modules/`
- CI/CD workflows: `.github/workflows/`
- Pre-commit config: `.pre-commit-config.yaml`

**Adapted from CliniCraft**:
- Auth module: `backend/app/auth/` (minimal changes)
- User service: `backend/app/services/user_service.py` (model changes only)
- Templates: `backend/app/templates/` (branding updates)
- Main app: `backend/app/main.py` (route differences)

### Common Pitfalls

- **Firestore indexes**: Not needed in Phase 1 (simple lookups only). Phase 2 will add indexes for queries.
- **Secret Manager**: Create secrets via Terraform, populate values manually via GCP Console.
- **JWT secret**: Generate secure random key, store in Secret Manager, not in code.
- **CORS**: Only enable in development. Remove for production.

### Deferred to Future Phases

- Garmin integration (Phase 2)
- Chat interface (Phase 3)
- Visualization generation (Phase 4)
- Goals tracking (Phase 5)
- Custom domain setup (Phase 6)
- Social features (Future)

---

## Dependencies for Next Phase

**Phase 2** (Garmin Integration) will need:
- ✅ User authentication working (JWT tokens)
- ✅ Firestore client configured
- ✅ Settings page for account linking
- ✅ User model with garmin_linked field
- ✅ Terraform infrastructure deployed

With Phase 1 complete, Phase 2 can add Garmin OAuth and data fetching on top of proven authentication foundation.

---

*Last Updated: 2025-11-11*
*Status: ⬜ TODO*
