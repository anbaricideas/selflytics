"""
Integration tests for chat-centric UI routing changes.

Phase 1: Core Backend Routes
- Root route redirects to /chat (not /dashboard)
- /dashboard redirects to /settings permanently (301)
- New /settings route requires authentication and renders template

Note: OAuth2PasswordRequestForm uses 'username' field for email in login requests.
      This is FastAPI's OAuth2 standard pattern.

Context: Chat-first navigation redesign
Spec: docs/development/chat-ui/SPECIFICATION.md lines 137-146, 378-422

E2E Coverage: Full authentication flows (login, token validation, redirects) are tested
in e2e_playwright tests which use real Firestore and actual authentication.
See: test_user_journeys.py, test_chat_ui_navigation.py, test_settings_navigation.py
"""

from fastapi.testclient import TestClient


# ===== Root Route Tests (Redirect to /chat) =====
# Note: Authenticated redirect covered by E2E test:
# test_authenticated_user_visiting_root_url_redirects_to_chat


def test_root_redirects_to_login_when_unauthenticated(client: TestClient):
    """
    Unauthenticated user visiting / should still redirect to /login.

    Expected: GET / → 303 redirect to /login
    Context: No change from existing behavior - unauthenticated users go to login
    """
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/login"


# ===== Dashboard Redirect Tests =====
# Note: Full redirect chain with auth covered by E2E test:
# test_old_dashboard_url_redirects_to_settings


def test_dashboard_redirect_does_not_require_authentication(client: TestClient):
    """
    Dashboard redirect should work for unauthenticated users too.

    Expected: GET /dashboard without auth → 301 redirect to /settings
    Context: Redirect happens before auth check (simpler implementation)
    """
    response = client.get("/dashboard", follow_redirects=False)

    # Should still redirect (auth check happens at /settings if needed)
    assert response.status_code == 301
    assert response.headers["location"] == "/settings"


# ===== Settings Route Tests =====
# Note: Settings rendering with auth covered by E2E test:
# test_navigate_from_settings_to_chat
# Note: Invalid token handling covered by E2E test:
# test_invalid_jwt_redirects_to_login


def test_settings_route_requires_authentication(client: TestClient):
    """
    Settings route should require authentication.

    Expected: GET /settings without auth → 401 or redirect to /login
    Context: Protected route - only authenticated users can access settings
    Spec: SPECIFICATION.md lines 142, 400-414
    """
    response = client.get("/settings", follow_redirects=False)

    # Should require auth - either 401 or redirect to login
    assert response.status_code in [303, 401], "Settings should require authentication"
    if response.status_code == 303:
        assert response.headers["location"] == "/login"
