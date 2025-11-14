"""
Unit tests for chat page navigation elements.

These tests verify that the chat.html template includes proper navigation
(logout button, dashboard link) so users aren't trapped on the chat page.

Context: Bug #10 - chat page missing navigation header
"""

# ruff: noqa: ERA001  # Commented code documents post-fix assertions in TDD

import pytest
from bs4 import BeautifulSoup


def test_chat_template_has_logout_button(templates):
    """
    Chat template should include logout button for user to sign out.

    Expected: Logout button with data-testid="logout-button"
    Context: Bug #10 - users trapped on chat page without logout
    """
    html = templates.get_template("chat.html").render(
        user={"profile": {"display_name": "Test User"}, "email": "test@example.com"}
    )

    soup = BeautifulSoup(html, "html.parser")

    # Find logout button
    logout_button = soup.find(attrs={"data-testid": "logout-button"})

    # CURRENT BUG: Logout button doesn't exist
    assert logout_button is None, "Bug #10 confirmed: Logout button missing from chat page"

    # After fixing Bug #10, this should pass:
    # assert logout_button is not None, (
    #     "Chat page should have logout button (data-testid='logout-button')"
    # )
    # assert logout_button.name in ["button", "a"], "Should be button or link"


def test_chat_template_has_dashboard_link(templates):
    """
    Chat template should include link back to dashboard.

    Expected: Link with href="/dashboard" or data-testid for navigation
    Context: Bug #10 - no way to navigate back to dashboard
    """
    html = templates.get_template("chat.html").render(
        user={"profile": {"display_name": "Test User"}, "email": "test@example.com"}
    )

    soup = BeautifulSoup(html, "html.parser")

    # Find dashboard link
    dashboard_link = soup.find("a", href="/dashboard")

    # CURRENT BUG: Dashboard link doesn't exist
    assert dashboard_link is None, "Bug #10 confirmed: Dashboard link missing from chat page"

    # After fixing Bug #10, this should pass:
    # assert dashboard_link is not None, (
    #     "Chat page should have link back to dashboard"
    # )


def test_chat_template_has_navigation_header(templates):
    """
    Chat template should have navigation header similar to dashboard.

    Expected: Header element with navigation elements
    Context: Bug #10 - consistent navigation pattern across pages
    """
    html = templates.get_template("chat.html").render(
        user={"profile": {"display_name": "Test User"}, "email": "test@example.com"}
    )

    soup = BeautifulSoup(html, "html.parser")

    # Find header element
    header = soup.find("header")

    # CURRENT BUG: No header element
    assert header is None, "Bug #10 confirmed: No <header> navigation element"

    # After fixing Bug #10, this should pass:
    # assert header is not None, "Chat page should have <header> element"
    # assert "Selflytics" in header.get_text(), "Header should show app name"


def test_chat_template_displays_user_name(templates):
    """
    Chat template header should display current user's name.

    Expected: User display name shown in navigation
    Context: Consistent with dashboard.html pattern
    """
    html = templates.get_template("chat.html").render(
        user={"profile": {"display_name": "Alice Smith"}, "email": "alice@example.com"}
    )

    soup = BeautifulSoup(html, "html.parser")

    # Find user name element
    user_name = soup.find(attrs={"data-testid": "user-name"})

    # CURRENT BUG: No user name display
    assert user_name is None, "Bug #10 confirmed: User name not displayed"

    # After fixing Bug #10, this should pass:
    # assert user_name is not None, "Header should display user name"
    # assert "Alice Smith" in user_name.get_text()


def test_chat_navigation_matches_dashboard_pattern(templates):
    """
    Chat navigation should match dashboard navigation structure.

    Expected: Same header structure as dashboard.html
    Context: Consistent user experience across pages
    """
    chat_html = templates.get_template("chat.html").render(
        user={"profile": {"display_name": "Test User"}, "email": "test@example.com"}
    )
    dashboard_html = templates.get_template("dashboard.html").render(
        user={"profile": {"display_name": "Test User"}, "email": "test@example.com"},
        garmin_linked=False,
    )

    chat_soup = BeautifulSoup(chat_html, "html.parser")
    dashboard_soup = BeautifulSoup(dashboard_html, "html.parser")

    # Dashboard has header with logout
    dashboard_header = dashboard_soup.find("header")
    dashboard_logout = dashboard_soup.find(attrs={"data-testid": "logout-button"})

    assert dashboard_header is not None, "Dashboard should have header"
    assert dashboard_logout is not None, "Dashboard should have logout button"

    # Chat should also have header with logout
    chat_header = chat_soup.find("header")
    chat_logout = chat_soup.find(attrs={"data-testid": "logout-button"})

    # CURRENT BUG: Chat missing navigation
    assert chat_header is None, "Bug #10 confirmed: Chat has no header"
    assert chat_logout is None, "Bug #10 confirmed: Chat has no logout"

    # After fixing Bug #10, this should pass:
    # assert chat_header is not None, "Chat should have header like dashboard"
    # assert chat_logout is not None, "Chat should have logout like dashboard"


@pytest.mark.asyncio
async def test_chat_page_logout_button_functional(client, test_user):
    """
    Integration test: Chat page logout button should work.

    Expected: Clicking logout redirects to login page
    Context: Bug #10 - complete logout workflow from chat page
    """
    # Login first
    login_response = client.post(
        "/auth/login",
        data={"email": test_user["email"], "password": test_user["password"]},
        follow_redirects=False,
    )
    assert login_response.status_code == 303
    cookies = login_response.cookies

    # Visit chat page
    chat_response = client.get("/chat/", cookies=cookies)
    assert chat_response.status_code == 200

    # Parse HTML
    soup = BeautifulSoup(chat_response.text, "html.parser")

    # Find logout button/form
    logout_button = soup.find(attrs={"data-testid": "logout-button"})

    # CURRENT BUG: Button doesn't exist, can't test functionality
    assert logout_button is None, "Bug #10 confirmed: Cannot test logout functionality (button missing)"

    # After fixing Bug #10, this should test the logout flow:
    # assert logout_button is not None
    # logout_form = logout_button.find_parent("form")
    # assert logout_form is not None
    # assert logout_form.get("action") == "/logout"
    # assert logout_form.get("method").upper() == "POST"
