# Development Workflow

This document describes the recommended development workflow for Selflytics.

## Core Principles

1. **Test-Driven Development (TDD)**: Write tests before implementation
2. **Local Testing First**: Validate locally before pushing to CI
3. **User Journey-Driven**: Design features from the user's perspective
4. **Commit Often**: Small, focused commits with clear messages

## Development Cycle

### For New Features

```
1. Write unit tests → Verify fail
2. Implement code → Verify tests pass
3. Write integration tests (if needed) → Verify pass
4. Write e2e tests (for user-facing features) → Verify pass locally
5. Run full test suite locally
6. Commit and push (triggers CI)
```

### Local Testing Commands

```bash
# Unit tests
uv --directory backend run pytest tests/unit -v

# Integration tests
uv --directory backend run pytest tests/integration -v

# E2E tests (local environment)
# Terminal 1: Start local server with emulator
./scripts/local-e2e-server.sh

# Terminal 2: Run e2e tests
uv --directory backend run pytest tests/e2e_playwright -v --headed

# All tests with coverage
uv --directory backend run pytest tests/ -v --cov=app
```

## E2E Testing Guidelines

### When to Write E2E Tests

Write e2e tests for:
- User registration and authentication flows
- Core user journeys (linking Garmin, asking questions, viewing data)
- Error recovery scenarios (invalid credentials, network failures)
- Critical business logic that spans multiple components

Skip e2e tests for:
- Internal utilities and helpers
- Pure data models
- Backend-only services without user interaction

### E2E Test Structure

**Each user journey test should cover**:
1. **Happy path**: User completes journey successfully
2. **Error recovery**: User encounters error, sees clear message, can retry
3. **Edge cases**: Unauthorized access, duplicate actions, boundary conditions

**Best practices**:
- Use `data-testid` attributes for selectors (not CSS classes)
- Test against local environment first (not CI preview)
- Mock external APIs (Garmin, OpenAI) for consistent tests
- Tag critical journeys with `@pytest.mark.critical` for pre-push hooks
- Keep test docstrings clear and reference user journeys

### Local E2E Testing Workflow

**Always test locally before push**:
1. Start local environment: `./scripts/local-e2e-server.sh`
2. Run e2e tests: `uv --directory backend run pytest tests/e2e_playwright -v --headed`
3. Fix any failures
4. Re-run tests until all pass
5. Stop local server (Ctrl+C)
6. Push to origin

**Why local first?**
- Fast feedback (30-60 seconds vs 5-10 minutes in CI)
- Easier debugging with `--headed` flag
- No waiting for deployments
- Catch issues before CI

## Manual Testing

While automated tests are essential, some scenarios require manual verification:

### When to Create Manual Runsheets

Create manual testing checklists for:
- New user-facing features with complex interactions
- Visual/UX changes that automated tests can't easily verify
- Accessibility requirements (screen reader testing)
- Cross-browser compatibility checks

### Manual Testing Process

1. Create runsheet: `docs/manual_testing/FEATURE_NAME_runsheet.md`
2. Execute tests manually, recording results
3. Note any gaps in automated test coverage
4. Add e2e tests for gaps discovered
5. Re-run automated tests to verify gap coverage

## Commit Guidelines

**Commit after**:
- Each logical unit of work (e.g., one component implemented with tests)
- All related tests pass
- Code is formatted and linted

**Commit message format**:
```
<type>: <description>

Examples:
feat: add Garmin OAuth flow
fix: correct token expiration handling
test: add e2e tests for registration journey
docs: update API documentation
```

**When to push**:
- After local tests pass (unit + integration + e2e)
- To trigger CI for full validation
- To share progress with team
- NOT after every single commit (batch related commits)

## Testing Requirements

### Coverage Standards

- **Unit tests**: 80%+ coverage required (CI enforced)
- **Integration tests**: Cover all API endpoints and service integrations
- **E2E tests**: Cover all critical user journeys

### Test Pyramid

- 60% unit tests (fast, isolated, comprehensive)
- 30% integration tests (moderate speed, test component interactions)
- 10% e2e tests (slower, test complete user flows)

### Quality Gates

Before marking work complete:
- ✅ All tests pass (unit + integration + e2e)
- ✅ 80%+ code coverage maintained
- ✅ No linting or type check errors
- ✅ All e2e tests pass locally
- ✅ Manual runsheet completed (if applicable)

## Common Issues and Solutions

### E2E Tests Fail in CI But Pass Locally

**Causes**:
- Environment differences (secrets, services)
- Timing issues (deployed app slower than local)
- Data state differences (emulator vs real Firestore)

**Solutions**:
- Check CI logs for specific errors
- Verify environment variables in deployment
- Add explicit waits for async operations
- Use consistent test data setup

### Slow E2E Test Execution

**Solutions**:
- Run critical tests only for quick feedback: `pytest -k "critical"`
- Use `--headed` only when debugging (headless is faster)
- Parallelize tests (if Playwright setup supports it)
- Mock external API calls to avoid network latency

### Pre-existing Test Failures

**Policy**: Never progress with failing tests, even if you didn't cause them.

**Actions**:
1. Investigate failure cause
2. Fix the test or the underlying bug
3. Ensure all tests pass before continuing
4. If unsure, ask for clarification

## Tools and Setup

### Required Tools

- **Python**: 3.12+ (managed via uv)
- **uv**: Package manager (not pip/poetry)
- **Playwright**: E2E testing framework
- **Firebase Emulator**: Local Firestore for e2e tests

### Environment Setup

Copy `.env.example` files and configure:
- **Root `.env`**: GCP project details
- **Backend `.env`**: JWT secrets, API keys (from Secret Manager)
- **Backend `.env.local`**: Local e2e testing configuration

**Never commit secrets**: Use GCP Secret Manager for real credentials.

## Reference Projects

When implementing features, check these for proven patterns:
- **CliniCraft** (`/Users/bryn/repos/clinicraft/`): Auth, Pydantic-AI, frontend patterns
- **Garmin Agents** (`/Users/bryn/repos/garmin_agents/`): Garmin OAuth, token encryption

## Getting Help

If blocked:
- Check existing test files for patterns
- Review phase plan for step-by-step guidance
- Consult reference projects for similar implementations
- Ask clarifying questions before making assumptions
