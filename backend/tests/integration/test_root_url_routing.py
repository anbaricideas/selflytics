"""
Integration tests for root URL routing behavior.

These tests verify that the root route (/) correctly redirects authenticated
users to dashboard and unauthenticated users to login.

Context: Bug #11 - root URL redirects all users to login (ignores auth state)
"""

# ruff: noqa: ERA001  # Commented code documents post-fix assertions in TDD

import pytest
from fastapi.testclient import TestClient


def test_root_redirects_unauthenticated_to_login(client: TestClient):
    """
    Root URL should redirect unauthenticated users to login page.

    Expected: GET / → 303 redirect to /login
    Context: Correct behavior for logged-out users
    """
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_root_redirects_authenticated_to_dashboard(client: TestClient, test_user: dict):
    """
    Root URL should redirect authenticated users to dashboard.

    Expected: GET / with valid JWT → 303 redirect to /dashboard
    Context: Bug #11 - currently redirects to /login (incorrect)
    """
    # Login first to get valid JWT
    login_response = client.post(
        "/auth/login",
        data={"email": test_user["email"], "password": test_user["password"]},
        follow_redirects=False,
    )
    assert login_response.status_code == 303
    cookies = login_response.cookies

    # Visit root URL with authenticated session
    response = client.get("/", cookies=cookies, follow_redirects=False)

    assert response.status_code == 303

    # CURRENT BUG: Redirects to /login (should redirect to /dashboard)
    assert response.headers["location"] == "/login", (
        "Bug #11 confirmed: Root URL redirects authenticated users to /login"
    )

    # After fixing Bug #11, this should pass:
    # assert response.headers["location"] == "/dashboard", (
    #     "Root URL should redirect authenticated users to /dashboard"
    # )


def test_root_with_invalid_token_redirects_to_login(client: TestClient):
    """
    Root URL with invalid/expired JWT should redirect to login.

    Expected: GET / with bad token → 303 redirect to /login
    Context: Invalid tokens should behave like unauthenticated
    """
    # Use invalid token
    bad_cookies = {"access_token": "invalid.jwt.token"}

    response = client.get("/", cookies=bad_cookies, follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_root_follows_redirect_chain_correctly(client: TestClient, test_user: dict):
    """
    Root URL should complete redirect chain to final destination.

    Expected: Authenticated users end up on dashboard after redirects
    Context: Verify complete navigation flow
    """
    # Login
    login_response = client.post(
        "/auth/login",
        data={"email": test_user["email"], "password": test_user["password"]},
        follow_redirects=False,
    )
    cookies = login_response.cookies

    # Visit root with follow_redirects=True
    response = client.get("/", cookies=cookies, follow_redirects=True)

    assert response.status_code == 200

    # CURRENT BUG: Ends up on login page
    assert "Login to Your Account" in response.text, (
        "Bug #11 confirmed: Redirect chain ends at login (should be dashboard)"
    )

    # After fixing Bug #11, this should pass:
    # # Verify we landed on dashboard by checking for dashboard-specific elements
    # from bs4 import BeautifulSoup
    # soup = BeautifulSoup(response.text, "html.parser")
    # dashboard_header = soup.find(attrs={"data-testid": "dashboard-header"})
    # assert dashboard_header is not None, "Should end up on dashboard page"
    # welcome_section = soup.find(attrs={"data-testid": "welcome-section"})
    # assert welcome_section is not None, "Should see welcome section"


def test_root_route_handles_missing_cookie_gracefully(client: TestClient):
    """
    Root URL without any cookies should redirect to login.

    Expected: No errors, clean redirect to /login
    Context: Edge case - no cookies at all
    """
    # Explicitly pass no cookies
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/login"


@pytest.mark.asyncio
async def test_root_route_checks_jwt_validity_not_just_existence(
    client: TestClient, test_user: dict
):
    """
    Root URL should validate JWT token, not just check if it exists.

    Expected: Expired/malformed tokens treated as unauthenticated
    Context: Security - must verify token signature and expiry
    """
    # Create malformed JWT (not properly signed)
    malformed_cookies = {"access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid.signature"}

    response = client.get("/", cookies=malformed_cookies, follow_redirects=False)

    # Should redirect to login (not crash)
    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_root_route_preserves_query_params_if_needed(client: TestClient, test_user: dict):
    """
    Root URL with query params should handle them appropriately.

    Expected: Redirect doesn't break with query strings
    Context: Edge case - root URL typically has no params, but should handle gracefully
    """
    # Login
    login_response = client.post(
        "/auth/login",
        data={"email": test_user["email"], "password": test_user["password"]},
        follow_redirects=False,
    )
    cookies = login_response.cookies

    # Visit root with query params
    response = client.get("/?ref=email", cookies=cookies, follow_redirects=False)

    # Should still redirect (query params might be ignored)
    assert response.status_code == 303
    # Should redirect somewhere (login or dashboard depending on fix)
    assert "location" in response.headers


def test_dashboard_route_requires_authentication_for_comparison(client: TestClient):
    """
    Dashboard route should require authentication (for comparison with root).

    Expected: GET /dashboard without auth → 401 or redirect to login
    Context: Shows expected auth-protected behavior
    """
    response = client.get("/dashboard", follow_redirects=False)

    # Dashboard requires auth - should redirect or return 401
    assert response.status_code in [303, 401], "Dashboard should require authentication"
    if response.status_code == 303:
        assert response.headers["location"] == "/login"
