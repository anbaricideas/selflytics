"""
Unit tests for chat page navigation elements.

These tests verify that the chat.html template includes proper navigation
(logout button, settings link) so users aren't trapped on the chat page.

Context: Bug #10 - chat page missing navigation header
Phase 4: Updated for chat-first navigation (settings icon replaced dashboard link)
"""

# Commented code documents post-fix assertions in TDD

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

    # Bug #10 fixed: Logout button now exists
    assert logout_button is not None, (
        "Chat page should have logout button (data-testid='logout-button')"
    )
    assert logout_button.name in ["button", "a"], "Should be button or link"


def test_chat_template_has_settings_link(templates):
    """
    Chat template should include link to settings page.

    Expected: Link with href="/settings" and data-testid="link-settings"
    Context: Phase 4 - Settings icon navigation (replaced dashboard link)
    """
    html = templates.get_template("chat.html").render(
        user={"profile": {"display_name": "Test User"}, "email": "test@example.com"}
    )

    soup = BeautifulSoup(html, "html.parser")

    # Find settings link
    settings_link = soup.find("a", href="/settings")

    assert settings_link is not None, "Chat page should have link to settings"
    assert settings_link.get("data-testid") == "link-settings", (
        "Settings link should have data-testid='link-settings'"
    )


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

    # Bug #10 fixed: Header element now exists
    assert header is not None, "Chat page should have <header> element"
    assert "Selflytics" in header.get_text(), "Header should show app name"


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

    # Bug #10 fixed: User name now displayed
    assert user_name is not None, "Header should display user name"
    assert "Alice Smith" in user_name.get_text()


def test_chat_navigation_has_settings_icon(templates):
    """
    Chat navigation should include settings icon link.

    Expected: Settings icon (SVG) within link to /settings
    Context: Phase 4 - Modern icon-based navigation pattern
    """
    chat_html = templates.get_template("chat.html").render(
        user={"profile": {"display_name": "Test User"}, "email": "test@example.com"}
    )

    chat_soup = BeautifulSoup(chat_html, "html.parser")

    # Chat should have header with logout and settings
    chat_header = chat_soup.find("header")
    chat_logout = chat_soup.find(attrs={"data-testid": "logout-button"})
    settings_link = chat_soup.find("a", href="/settings")

    assert chat_header is not None, "Chat should have header"
    assert chat_logout is not None, "Chat should have logout button"
    assert settings_link is not None, "Chat should have settings link"

    # Settings link should contain SVG icon
    settings_svg = settings_link.find("svg")
    assert settings_svg is not None, "Settings link should contain SVG icon"


@pytest.mark.skip(reason="Integration test - should be in integration/ folder")
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

    # Bug #10 fixed: Button exists, test logout functionality
    assert logout_button is not None
    logout_form = logout_button.find_parent("form")
    assert logout_form is not None
    assert logout_form.get("action") == "/logout"
    assert logout_form.get("method").upper() == "POST"
