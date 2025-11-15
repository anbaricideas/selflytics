"""Integration tests for CSRF protection on routes."""

from bs4 import BeautifulSoup
from fastapi.testclient import TestClient


def test_register_requires_csrf_token(client: TestClient):
    """Test that /auth/register rejects requests without CSRF token."""
    response = client.post(
        "/auth/register",
        data={
            "email": "test@example.com",
            "password": "TestPass123",
            "display_name": "Test User",
            "confirm_password": "TestPass123",
            # csrf_token intentionally omitted
        },
    )

    assert response.status_code == 403
    assert "CSRF" in response.text or "Security validation" in response.text


def test_register_with_valid_csrf_token(client: TestClient):
    """Test that /auth/register accepts valid CSRF token."""
    # Get form with CSRF token
    form_response = client.get("/register")
    assert form_response.status_code == 200

    # Extract CSRF token from cookie (library uses 'fastapi-csrf-token' as cookie name)
    csrf_cookie = form_response.cookies.get("fastapi-csrf-token")
    assert csrf_cookie is not None

    # Extract CSRF token from HTML (form field name is 'csrf_token')
    soup = BeautifulSoup(form_response.text, "html.parser")
    csrf_input = soup.find("input", {"name": "fastapi-csrf-token"})
    assert csrf_input is not None
    csrf_token = csrf_input["value"]

    # Submit form with valid token
    response = client.post(
        "/auth/register",
        data={
            "email": "newuser@example.com",
            "password": "TestPass123",
            "display_name": "New User",
            "confirm_password": "TestPass123",
            "fastapi-csrf-token": csrf_token,  # form field name
        },
        cookies={"fastapi-csrf-token": csrf_cookie},  # cookie name
    )

    # Should succeed (or fail with email exists, not CSRF error)
    assert response.status_code in (200, 400)
    if response.status_code == 400:
        # If 400, should be email exists, not CSRF error
        assert "CSRF" not in response.text


def test_csrf_token_rotation_on_register_error(client: TestClient):
    """Test that CSRF token is rotated when registration has validation errors."""
    # Get initial form
    form1 = client.get("/register")
    cookie1 = form1.cookies.get("fastapi-csrf-token")

    soup = BeautifulSoup(form1.text, "html.parser")
    csrf_token1 = soup.find("input", {"name": "fastapi-csrf-token"})["value"]

    # Submit with password mismatch error
    response = client.post(
        "/auth/register",
        data={
            "email": "test@example.com",
            "password": "Pass123",
            "confirm_password": "Pass456",  # Mismatch!
            "display_name": "Test",
            "fastapi-csrf-token": csrf_token1,
        },
        cookies={"fastapi-csrf-token": cookie1},
        headers={"HX-Request": "true"},
    )

    assert response.status_code == 400
    assert "Passwords do not match" in response.text

    # Token should be rotated
    cookie2 = response.cookies.get("fastapi-csrf-token")
    assert cookie2 is not None
    assert cookie2 != cookie1  # Different cookie!

    # Extract new token from returned form fragment
    soup2 = BeautifulSoup(response.text, "html.parser")
    csrf_input2 = soup2.find("input", {"name": "fastapi-csrf-token"})
    assert csrf_input2 is not None
    csrf_token2 = csrf_input2["value"]
    assert csrf_token2 != csrf_token1  # Different token value!


def test_login_requires_csrf_token(client: TestClient):
    """Test that /auth/login rejects requests without CSRF token."""
    response = client.post(
        "/auth/login",
        data={
            "username": "test@example.com",
            "password": "TestPass123",
            # csrf_token intentionally omitted
        },
    )

    assert response.status_code == 403
    assert "CSRF" in response.text or "Security validation" in response.text


def test_login_with_valid_csrf_token(client: TestClient):
    """Test that /auth/login accepts valid CSRF token."""
    # Get form with CSRF token
    form_response = client.get("/login")
    assert form_response.status_code == 200

    # Extract CSRF token
    csrf_cookie = form_response.cookies.get("fastapi-csrf-token")
    soup = BeautifulSoup(form_response.text, "html.parser")
    csrf_token = soup.find("input", {"name": "fastapi-csrf-token"})["value"]

    # Submit with valid token (will fail auth but not CSRF)
    response = client.post(
        "/auth/login",
        data={
            "username": "test@example.com",
            "password": "WrongPassword",
            "fastapi-csrf-token": csrf_token,
        },
        cookies={"fastapi-csrf-token": csrf_cookie},
    )

    # Should fail auth (401 or 400), not CSRF (403)
    assert response.status_code in (400, 401)
    assert "CSRF" not in response.text


def test_csrf_token_rotation_on_login_error(client: TestClient):
    """Test that CSRF token is rotated on login failure."""
    # Get initial form
    form1 = client.get("/login")
    cookie1 = form1.cookies.get("fastapi-csrf-token")
    soup1 = BeautifulSoup(form1.text, "html.parser")
    csrf_token1 = soup1.find("input", {"name": "fastapi-csrf-token"})["value"]

    # Submit with wrong credentials
    response = client.post(
        "/auth/login",
        data={
            "username": "test@example.com",
            "password": "WrongPassword",
            "fastapi-csrf-token": csrf_token1,
        },
        cookies={"fastapi-csrf-token": cookie1},
        headers={"HX-Request": "true"},
    )

    assert response.status_code in (400, 401)

    # Token should be rotated
    cookie2 = response.cookies.get("fastapi-csrf-token")
    assert cookie2 is not None
    assert cookie2 != cookie1

    # Extract new token from form
    soup2 = BeautifulSoup(response.text, "html.parser")
    csrf_input2 = soup2.find("input", {"name": "fastapi-csrf-token"})
    assert csrf_input2 is not None
    csrf_token2 = csrf_input2["value"]
    assert csrf_token2 != csrf_token1
