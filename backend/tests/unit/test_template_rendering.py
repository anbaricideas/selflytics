"""Unit tests for template rendering and HTML structure.

Tests verify that templates render correctly with proper data-testid attributes
and contain expected structural elements.
"""

from unittest.mock import AsyncMock


def test_login_template_renders_successfully(unauthenticated_client):
    """Login template should render without errors."""
    response = unauthenticated_client.get("/login")

    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")

    html = response.text
    # Should contain core structural elements
    assert "<form" in html
    assert 'hx-post="/auth/login"' in html
    assert "Login" in html or "login" in html


def test_register_template_renders_successfully(unauthenticated_client):
    """Register template should render without errors."""
    response = unauthenticated_client.get("/register")

    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")

    html = response.text
    assert "<form" in html
    assert 'hx-post="/auth/register"' in html
    assert "Register" in html or "register" in html or "Create Account" in html


def test_dashboard_template_renders_for_authenticated_user(client, test_user_token):
    """Dashboard template should render for authenticated users."""
    response = client.get(
        "/dashboard",
        headers={"Authorization": f"Bearer {test_user_token}"},
    )

    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")

    html = response.text
    assert "Dashboard" in html or "dashboard" in html
    assert "Welcome" in html or "welcome" in html


def test_garmin_settings_template_renders_for_authenticated_user(client, test_user_token):
    """Garmin settings template should render for authenticated users."""
    response = client.get(
        "/garmin/link",
        headers={"Authorization": f"Bearer {test_user_token}"},
    )

    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")

    html = response.text
    assert "<form" in html
    assert 'hx-post="/garmin/link"' in html
    assert "Garmin" in html or "garmin" in html


def test_templates_include_htmx_script(unauthenticated_client):
    """All pages should include HTMX script tag."""
    pages = ["/login", "/register"]

    for page in pages:
        response = unauthenticated_client.get(page)
        html = response.text

        # Should include HTMX library
        assert "htmx.org" in html or "htmx" in html.lower(), f"Page {page} missing HTMX script"


def test_templates_include_alpine_script(unauthenticated_client):
    """All pages should include Alpine.js script tag."""
    pages = ["/login", "/register"]

    for page in pages:
        response = unauthenticated_client.get(page)
        html = response.text

        # Should include Alpine.js library
        assert "alpinejs" in html.lower() or "alpine" in html.lower(), (
            f"Page {page} missing Alpine.js script"
        )


def test_templates_include_tailwind_css(unauthenticated_client):
    """All pages should include Tailwind CSS."""
    pages = ["/login", "/register"]

    for page in pages:
        response = unauthenticated_client.get(page)
        html = response.text

        # Should include Tailwind CSS
        assert "tailwindcss" in html.lower(), f"Page {page} missing Tailwind CSS"


def test_error_template_with_validation_errors(unauthenticated_client, create_mock_user):
    """Register template should display validation errors when present."""
    from app.auth.dependencies import get_user_service
    from app.main import app

    mock_svc = AsyncMock()
    # Mock existing user to trigger error
    mock_svc.get_user_by_email.return_value = create_mock_user(email="existing@example.com")

    app.dependency_overrides[get_user_service] = lambda: mock_svc

    try:
        response = unauthenticated_client.post(
            "/auth/register",
            data={
                "email": "existing@example.com",
                "password": "Password123!",
                "display_name": "Test",
            },
            headers={"HX-Request": "true"},
        )

        assert response.status_code == 400
        html = response.text

        # Should contain error message
        assert "already registered" in html.lower() or "error" in html.lower()
        # Should still contain form for retry
        assert "<form" in html
    finally:
        app.dependency_overrides.clear()


def test_templates_have_proper_html_structure(unauthenticated_client):
    """Templates should have proper HTML5 structure."""
    response = unauthenticated_client.get("/login")
    html = response.text.lower()

    # Should have HTML5 doctype
    assert "<!doctype html>" in html

    # Should have required tags
    assert "<html" in html
    assert "<head>" in html
    assert "<body" in html
    assert "</html>" in html

    # Should have meta tags
    assert "<meta charset" in html
    assert '<meta name="viewport"' in html


def test_templates_have_accessible_labels(unauthenticated_client):
    """Form inputs should have associated labels for accessibility."""
    response = unauthenticated_client.get("/login")
    html = response.text

    # Each input should have a label
    # Count inputs (excluding hidden)
    visible_inputs = html.count('type="email"') + html.count('type="password"')

    # Count labels
    labels = html.count("<label")

    # Should have at least as many labels as visible inputs
    assert labels >= visible_inputs, "Some inputs missing labels for accessibility"
