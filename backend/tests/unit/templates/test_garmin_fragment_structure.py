"""
Unit tests for Garmin link form fragment structure.

These tests verify that the garmin_link_form.html fragment follows
the same pattern as login_form.html and register_form.html to avoid
duplicate headers when HTMX swaps error responses.

Context: Bug #9 - garmin_link_form has outer <div> wrapper causing header duplication
"""

# Commented code documents post-fix assertions in TDD

import pytest
from bs4 import BeautifulSoup


def test_garmin_link_fragment_has_no_outer_div_wrapper(templates):
    """
    Garmin link fragment should have <form> as root element, not <div>.

    Expected: Fragment starts with <form> tag (like login/register fragments)
    Context: Bug #9 - outer <div> causes duplicate headers with hx-swap="outerHTML"
    """
    # Render the fragment with error (worst case for duplication)
    html = templates.get_template("fragments/garmin_link_form.html").render(
        error_message="Invalid credentials"
    )

    soup = BeautifulSoup(html, "html.parser")

    # Find root element (should be <form>)
    root_elements = [
        child
        for child in soup.children
        if child.name is not None  # Skip text nodes
    ]

    # Should have exactly one root element
    assert len(root_elements) == 1, (
        f"Fragment should have single root element, found {len(root_elements)}: "
        f"{[el.name for el in root_elements]}"
    )

    root = root_elements[0]

    # Bug #9 fixed: Root is now <form> (was <div>)
    assert root.name == "form", (
        f"Fragment root should be <form>, not <{root.name}>. "
        "This ensures HTMX outerHTML swap doesn't duplicate containers."
    )


def test_garmin_link_fragment_header_inside_form(templates):
    """
    Garmin link fragment header should be inside <form>, not in outer wrapper.

    Expected: "Link Your Garmin Account" header is child of <form>
    Context: Bug #9 - header in outer <div> gets duplicated on error swap
    """
    html = templates.get_template("fragments/garmin_link_form.html").render()

    soup = BeautifulSoup(html, "html.parser")

    # Find the header
    header = soup.find("h2", string="Link Your Garmin Account")
    assert header is not None, "Fragment should contain 'Link Your Garmin Account' header"

    # Find the form
    form = soup.find("form")
    assert form is not None, "Fragment should contain <form> element"

    # Bug #9 fixed: Header is now inside form (was in outer div)
    assert header.find_parent("form") is not None, (
        "Header should be inside <form> element to prevent duplication. "
        "With hx-swap='outerHTML', entire form gets replaced (including header)."
    )


def test_garmin_link_fragment_matches_auth_fragment_pattern(templates):
    """
    Garmin link fragment should match login/register fragment structure.

    Expected: Same nesting pattern as login_form.html
    Context: Bug #9 - inconsistent structure causes HTMX swap issues
    """
    # Render all three fragments
    garmin_html = templates.get_template("fragments/garmin_link_form.html").render(
        error_message="Test error"
    )
    login_html = templates.get_template("fragments/login_form.html").render(
        error_message="Test error"
    )

    garmin_soup = BeautifulSoup(garmin_html, "html.parser")
    login_soup = BeautifulSoup(login_html, "html.parser")

    # Get root elements
    garmin_root = next(child for child in garmin_soup.children if child.name)
    login_root = next(child for child in login_soup.children if child.name)

    # Bug #9 fixed: Root elements now match
    assert garmin_root.name == login_root.name, (
        f"Garmin fragment should match login fragment structure. "
        f"Got <{garmin_root.name}> vs <{login_root.name}>"
    )


def test_garmin_link_fragment_error_message_inside_form(templates):
    """
    Error messages should be inside <form>, not in outer wrapper.

    Expected: Error div is child of <form> element
    Context: Ensures error appears/disappears with form swap
    """
    html = templates.get_template("fragments/garmin_link_form.html").render(
        error_message="Invalid Garmin credentials"
    )

    soup = BeautifulSoup(html, "html.parser")

    # Find error message div
    error_div = soup.find("div", class_="bg-red-50")
    assert error_div is not None, "Error message should be rendered"

    # Find the form
    form = soup.find("form")
    assert form is not None, "Fragment should contain form"

    # Bug #9 fixed: Error is now inside form (was in outer div)
    assert error_div.find_parent("form") is not None, (
        "Error message should be inside <form> so it swaps together with form"
    )


@pytest.mark.skip(reason="Integration test - should be in integration/ folder")
@pytest.mark.asyncio
async def test_garmin_link_fragment_used_by_error_response(client, test_user):
    """
    Integration test: Error responses should return the fragment with single root.

    Expected: POST /garmin/link error returns fragment with <form> root
    Context: Bug #9 - ensures backend uses correct fragment
    """
    # Login first
    login_response = client.post(
        "/auth/login",
        data={"email": test_user["email"], "password": test_user["password"]},
        follow_redirects=False,
    )
    assert login_response.status_code == 303

    # Extract cookie
    cookies = login_response.cookies

    # Submit invalid Garmin credentials
    response = client.post(
        "/garmin/link",
        data={"garmin_email": "invalid@garmin.com", "garmin_password": "wrong"},
        cookies=cookies,
        headers={"HX-Request": "true"},  # HTMX request
    )

    # Should return HTML fragment
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]

    # Parse HTML
    soup = BeautifulSoup(response.text, "html.parser")

    # Get root element
    root_elements = [child for child in soup.children if child.name is not None]
    assert len(root_elements) == 1, "Should return single root element"

    root = root_elements[0]

    # Bug #9 fixed: Returns <form> root (was <div> wrapper)
    assert root.name == "form", "Error response should return <form> as root element"
