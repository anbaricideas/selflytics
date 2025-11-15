# MyPy Type Checking Setup - Migration Notes

> **Note**: This document describes the mypy migration process (completed in PR #9).
> See `docs/DEVELOPMENT_WORKFLOW.md` for current type checking guidelines.

This document contains historical notes from the mypy type checking setup for Selflytics.

## What Has Been Done

✅ **Configuration files updated**:
- Added `mypy>=1.8.0` to dev dependencies in `backend/pyproject.toml`
- Created strict mypy configuration in `backend/pyproject.toml` with:
  - Python 3.12 target
  - Strict mode enabled
  - Configured to ignore missing imports for third-party libraries (garth, pydantic_ai, google.cloud, etc.)
- Added mypy to pre-commit hooks in `.pre-commit-config.yaml`
- Updated `docs/DEVELOPMENT_WORKFLOW.md` with type checking guidelines

## What Needs to Be Done Manually

### 1. Install Dependencies

```bash
# From project root
uv sync --all-extras --directory backend
```

### 2. Run MyPy to Identify Type Errors

```bash
# From project root
uv --directory backend run mypy app
```

This will show all type errors in the codebase. Expected output will include errors for:
- Missing type annotations on functions
- Incomplete type hints (e.g., `-> None` missing on async functions)
- Any type mismatches

### 3. Fix Type Errors

**Strategy**: Fix errors incrementally, focusing on one module at a time. Start with utilities and models, then move to services and routes.

**Common fixes needed**:

#### Missing return type annotations
```python
# Before
async def my_function(arg: str):
    return {"result": arg}

# After
async def my_function(arg: str) -> dict[str, str]:
    return {"result": arg}
```

#### Untyped function parameters
```python
# Before
def process_data(items):
    return [item.upper() for item in items]

# After
def process_data(items: list[str]) -> list[str]:
    return [item.upper() for item in items]
```

#### Optional types
```python
# Before
def get_user(user_id: str) -> User:  # May return None!
    user = db.get(user_id)
    return user

# After
def get_user(user_id: str) -> User | None:
    user = db.get(user_id)
    return user
```

#### TYPE_CHECKING imports (for circular dependencies)
```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.user import User  # Only imported for type checking

def process_user(user_data: dict[str, str]) -> "User":
    # Use string literal for forward reference
    ...
```

### 4. Update CI Workflow

**File**: `.github/workflows/ci.yml` (lines 183-213)

Replace the current `type-check` job with:

```yaml
  # Type check runs on: push to main, or non-draft PRs
  # Skipped for draft PRs to provide faster feedback
  type-check:
    name: Type Check
    runs-on: ubuntu-latest
    if: github.event_name == 'push' || (github.event_name == 'pull_request' && github.event.pull_request.draft == false)
    defaults:
      run:
        working-directory: backend

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}

      - name: Install uv
        uses: astral-sh/setup-uv@v5
        with:
          version: "latest"
          enable-cache: true
          cache-dependency-glob: "backend/uv.lock"

      - name: Install dependencies
        run: uv sync --all-extras

      - name: Run mypy type checking
        run: uv run mypy app --strict
```

**Key changes**:
- Removed `continue-on-error: true` to make type checking blocking
- Changed command from `ruff check --select=TCH` to `mypy app --strict`
- This will enforce type checking in CI

### 5. Update Pre-commit Hooks

```bash
# From project root
pre-commit install
pre-commit autoupdate
```

### 6. Test the Setup

```bash
# Run mypy locally
uv --directory backend run mypy app --strict

# Should output: Success: no issues found in X source files

# Test pre-commit hook
git add .
git commit -m "test: verify mypy pre-commit hook"
# MyPy should run automatically and block commit if errors exist
```

### 7. Verify CI Integration

Once the CI workflow is updated:
1. Push changes to a branch
2. Open a PR
3. Verify that the `Type Check` job runs in CI
4. Verify it fails if type errors exist
5. Fix any errors and push again
6. Verify it passes when code is correctly typed

## Common Type Issues to Watch For

### 1. Firestore Types
The `google-cloud-firestore` library has incomplete type stubs. You may need to add explicit types:

```python
from google.cloud.firestore import DocumentReference, DocumentSnapshot

def get_doc(doc_ref: DocumentReference) -> dict[str, Any] | None:
    doc: DocumentSnapshot = doc_ref.get()
    return doc.to_dict() if doc.exists else None
```

### 2. FastAPI Dependencies
FastAPI's `Depends()` can cause type issues. Use type annotations:

```python
from typing import Annotated
from fastapi import Depends

async def get_current_user(...) -> User:
    ...

CurrentUser = Annotated[User, Depends(get_current_user)]

@router.get("/profile")
async def get_profile(user: CurrentUser) -> dict[str, str]:
    return {"email": user.email}
```

### 3. Async Functions
All async functions must have return type annotations:

```python
# Wrong
async def my_func():
    await some_operation()

# Correct
async def my_func() -> None:
    await some_operation()
```

### 4. Pydantic Models
Pydantic models generally work well with mypy, but watch for:

```python
from pydantic import BaseModel

class MyModel(BaseModel):
    value: str

# This is fine - Pydantic provides good type hints
def process(model: MyModel) -> str:
    return model.value
```

## Testing After Fixes

After fixing type errors:

```bash
# 1. Run mypy
uv --directory backend run mypy app --strict

# 2. Run tests to ensure no behavior changes
uv --directory backend run pytest tests/ -v

# 3. Run linting
uv --directory backend run ruff check .

# 4. Run formatting
uv --directory backend run ruff format .

# 5. Try a commit (will trigger pre-commit hooks)
git add .
git commit -m "fix: add type annotations for mypy compliance"
```

## Expected Outcome

When complete:
- ✅ `uv run mypy app --strict` passes with no errors
- ✅ Pre-commit hook catches type errors before commit
- ✅ CI fails if type errors are introduced
- ✅ All tests still pass (no behavior changes)
- ✅ Code coverage maintained at 80%+

## Notes

- **Use strict mode**: The configuration uses `--strict` to enforce best practices
- **Modern syntax**: Use `list[str]` not `List[str]` (Python 3.12+)
- **No behavior changes**: Type hints are purely for static analysis, they don't change runtime behavior
- **Incremental adoption**: Fix one module at a time, starting with utilities and models
- **Ask for help**: If a type error is unclear, check mypy documentation or ask for clarification

## Reference

- MyPy documentation: https://mypy.readthedocs.io/
- FastAPI + MyPy: https://fastapi.tiangolo.com/advanced/advanced-dependencies/
- Pydantic + MyPy: https://docs.pydantic.dev/latest/integrations/mypy/
