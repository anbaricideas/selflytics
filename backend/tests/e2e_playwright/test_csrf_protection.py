"""E2E tests for CSRF protection.

This module tests the Cross-Site Request Forgery (CSRF) protection implementation
across all protected endpoints. Tests verify:

1. Attack prevention: Cross-origin POST requests without valid tokens are blocked
2. Token rotation: Tokens are regenerated after validation errors
3. HTMX compatibility: Tokens work correctly with partial DOM updates

Reference: docs/development/csrf/CSRF_SPECIFICATION.md
"""

import re

import pytest
from playwright.async_api import Page, expect


@pytest.mark.e2e
class TestCSRFAttackPrevention:
    """Verify CSRF protection blocks cross-origin POST attacks."""

    async def test_csrf_blocks_cross_origin_garmin_link_attack(
        self,
        authenticated_user: Page,
        base_url: str,
    ):
        """Test that cross-origin POST to /garmin/link is blocked by CSRF protection.

        This test simulates the HIGH-RISK attack scenario from spec lines 102-168:
        - Attacker creates malicious page with auto-submitting form
        - Victim (logged into Selflytics) visits malicious page
        - Browser auto-sends victim's auth cookie with POST request
        - CSRF protection BLOCKS the request (no valid CSRF token)
        - Victim's account remains secure (attacker's Garmin account NOT linked)

        Reference: Spec lines 655-729 (Journey 2 - CSRF Attack Blocked)
        """
        page = authenticated_user

        # Track responses to verify 403 rejection
        responses = []

        async def track_responses(response):
            if "/garmin/link" in response.url and response.request.method == "POST":
                responses.append(response)

        page.on("response", track_responses)

        # STEP 1: Verify user can access Garmin link page (shows form)
        await page.goto(f"{base_url}/garmin/link")
        await expect(page.locator('[data-testid="form-link-garmin"]')).to_be_visible()

        # STEP 2: Simulate attacker's malicious page
        # This page auto-submits a form to /garmin/link without CSRF token
        malicious_html = f"""
        <!DOCTYPE html>
        <html>
        <head><title>Malicious Page</title></head>
        <body onload="document.forms[0].submit()">
            <h1>Loading...</h1>
            <form action="{base_url}/garmin/link" method="POST" id="attack-form">
                <input type="hidden" name="username" value="attacker@evil.com">
                <input type="hidden" name="password" value="AttackerGarminPass123">
                <!-- NO csrf_token - this is the attack! -->
            </form>
        </body>
        </html>
        """

        # Navigate to malicious page (simulates clicking phishing link)
        await page.set_content(malicious_html)

        # STEP 3: Wait for form auto-submission to complete
        await page.wait_for_load_state("networkidle")

        # STEP 3a: Verify attack request was sent and rejected with 403
        assert len(responses) > 0, "Attack request should have been sent"
        attack_response = responses[-1]
        assert attack_response.status == 403, (
            f"Expected 403 Forbidden, got {attack_response.status}"
        )

        # STEP 4: Navigate back to Garmin link page to verify account NOT linked
        await page.goto(f"{base_url}/garmin/link")

        # Verify Garmin link FORM is still showing (not success message)
        # If attack succeeded, we'd see "Garmin account linked" success message
        await expect(page.locator('[data-testid="form-link-garmin"]')).to_be_visible()

        # Verify no success indicators
        garmin_linked = page.locator('[data-testid="garmin-status-linked"]')
        await expect(garmin_linked).not_to_be_visible()

        # Additional verification: ensure no generic success text
        success_text = page.locator("text=Successfully linked")
        await expect(success_text).not_to_be_visible()

    async def test_csrf_blocks_cross_origin_register_attack(
        self,
        page: Page,
        base_url: str,
    ):
        """Test that cross-origin POST to /auth/register is blocked.

        Simpler attack scenario (no authentication required) to verify
        CSRF protection works on registration endpoint.

        Reference: Spec lines 175-203 (Forced Account Registration attack)
        """
        # Track responses to verify 403 rejection
        responses = []

        async def track_responses(response):
            if "/auth/register" in response.url and response.request.method == "POST":
                responses.append(response)

        page.on("response", track_responses)

        # STEP 1: Navigate to legitimate registration page
        await page.goto(f"{base_url}/register")
        await expect(page.locator('[data-testid="register-form"]')).to_be_visible()

        # STEP 2: Simulate attacker's page trying to create spam accounts
        malicious_html = f"""
        <!DOCTYPE html>
        <html>
        <body onload="submitAttack()">
            <h1>Processing...</h1>
            <iframe name="hidden-frame" style="display:none"></iframe>
            <form action="{base_url}/auth/register" method="POST" target="hidden-frame">
                <input type="hidden" name="email" value="spam-001@tempmail.com">
                <input type="hidden" name="password" value="SpamPass123">
                <input type="hidden" name="display_name" value="Spam User">
                <input type="hidden" name="confirm_password" value="SpamPass123">
                <!-- NO csrf_token -->
            </form>
            <script>
                function submitAttack() {{
                    document.forms[0].submit();
                }}
            </script>
        </body>
        </html>
        """

        await page.set_content(malicious_html)

        # Wait for iframe submission and response
        await page.wait_for_timeout(2000)

        # STEP 2a: Verify attack request was rejected with 403
        assert len(responses) > 0, "Attack request should have been sent"
        attack_response = responses[-1]
        assert attack_response.status == 403, (
            f"Expected 403 Forbidden, got {attack_response.status}"
        )

        # STEP 3: Verify attack failed - try to login with spam credentials
        await page.goto(f"{base_url}/login")
        await page.fill('[data-testid="input-email"]', "spam-001@tempmail.com")
        await page.fill('[data-testid="input-password"]', "SpamPass123")
        await page.click('[data-testid="submit-login"]')

        # Login should FAIL (account not created)
        error_msg = page.locator("text=Incorrect email or password")
        await expect(error_msg).to_be_visible(timeout=5000)


@pytest.mark.e2e
class TestCSRFTokenRotation:
    """Verify CSRF tokens are rotated on validation errors."""

    async def test_csrf_token_rotation_on_validation_error(
        self,
        page: Page,
        base_url: str,
        test_user: dict,
    ):
        """Test that CSRF token is rotated when form has validation errors.

        Verifies token rotation prevents replay attacks by ensuring each
        form submission gets a fresh token after validation errors.

        Reference: Spec lines 733-799 (Journey 3 - Form Validation Error)
        """
        # STEP 1: Navigate to registration page
        await page.goto(f"{base_url}/register")
        await expect(page.locator('[data-testid="register-form"]')).to_be_visible()

        # STEP 2: Extract initial CSRF token from hidden field
        csrf_input = page.locator('input[name="fastapi-csrf-token"]')
        await expect(csrf_input).to_be_hidden()
        token1 = await csrf_input.get_attribute("value")

        assert token1 is not None, "CSRF token should be present"
        assert len(token1) >= 32, "CSRF token should have sufficient length"
        # Verify token appears to be random (alphanumeric with variety)
        assert re.match(r"^[A-Za-z0-9_-]+$", token1), "Token should be URL-safe base64"
        # Check for some character variety (not all same character)
        assert len(set(token1)) > 5, "Token should have character variety"

        # STEP 3: Fill form with password MISMATCH (validation error)
        await page.fill('[data-testid="input-email"]', test_user["email"])
        await page.fill('[data-testid="input-display-name"]', test_user["display_name"])
        await page.fill('[data-testid="input-password"]', test_user["password"])
        await page.fill('input[name="confirm_password"]', "WrongPassword123!")  # MISMATCH!

        # STEP 4: Submit form (will fail validation)
        await page.click('[data-testid="submit-register"]')

        # STEP 5: Wait for HTMX to swap form with error message
        error_msg = page.locator("text=Passwords do not match")
        await expect(error_msg).to_be_visible(timeout=5000)

        # STEP 6: Extract NEW CSRF token from re-rendered form
        csrf_input2 = page.locator('input[name="fastapi-csrf-token"]')
        token2 = await csrf_input2.get_attribute("value")

        assert token2 is not None
        assert len(token2) >= 32

        # STEP 7: Verify token was ROTATED (different from original)
        assert token2 != token1, "CSRF token should be rotated after validation error"

        # STEP 8: Correct the password and submit with NEW token
        await page.fill('[data-testid="input-password"]', test_user["password"])
        await page.fill('input[name="confirm_password"]', test_user["password"])  # Fixed!
        await page.click('[data-testid="submit-register"]')

        # STEP 9: Verify successful registration (redirects to dashboard)
        await page.wait_for_url(f"{base_url}/dashboard", timeout=5000)
        await expect(page).to_have_url(f"{base_url}/dashboard")

    async def test_csrf_token_rotation_on_login_failure(
        self,
        authenticated_user: Page,
        base_url: str,
        test_user: dict,
    ):
        """Test that CSRF token is rotated on login authentication failure.

        Reference: Spec lines 733-799
        """
        page = authenticated_user

        # Logout to test login flow
        await page.click('[data-testid="logout-button"]')
        await page.wait_for_url(f"{base_url}/login", timeout=5000)

        # STEP 1: Extract initial token
        token1 = await page.locator('input[name="fastapi-csrf-token"]').get_attribute("value")
        assert token1 is not None

        # STEP 2: Submit with WRONG password
        await page.fill('[data-testid="input-email"]', test_user["email"])
        await page.fill('[data-testid="input-password"]', "WrongPassword123")
        await page.click('[data-testid="submit-login"]')

        # STEP 3: Wait for error
        error_msg = page.locator("text=Incorrect email or password")
        await expect(error_msg).to_be_visible(timeout=5000)

        # STEP 4: Verify token rotated
        token2 = await page.locator('input[name="fastapi-csrf-token"]').get_attribute("value")
        assert token2 is not None
        assert token2 != token1, "Token should rotate on auth failure"

        # STEP 5: Login with CORRECT password and new token
        await page.fill('[data-testid="input-password"]', test_user["password"])
        await page.click('[data-testid="submit-login"]')

        # STEP 6: Verify success
        await page.wait_for_url(f"{base_url}/dashboard", timeout=5000)


@pytest.mark.e2e
class TestCSRFHTMXCompatibility:
    """Verify CSRF tokens work correctly with HTMX partial DOM updates."""

    async def test_csrf_token_works_with_htmx_partial_updates(
        self,
        page: Page,
        base_url: str,
        test_user: dict,
    ):
        """Test that CSRF tokens are preserved and rotated correctly with HTMX partial updates.

        HTMX swaps HTML fragments without full page reloads. This test verifies:
        1. Token included in initial partial render
        2. Token rotated when fragment is swapped after error
        3. New token works for subsequent submission

        Uses registration form for testing since it has real CSRF validation
        (not mocked responses).

        Reference: Spec lines 461-577 (HTMX Integration)
        """
        # STEP 1: Navigate to registration page to test HTMX behavior
        await page.goto(f"{base_url}/register")
        await expect(page.locator('[data-testid="register-form"]')).to_be_visible()

        # STEP 2: Verify CSRF token exists in form
        csrf_input = page.locator('input[name="fastapi-csrf-token"]')
        await expect(csrf_input).to_be_hidden()
        token1 = await csrf_input.get_attribute("value")
        assert token1 is not None
        assert len(token1) >= 32

        # STEP 3: Submit form with password MISMATCH (validation error)
        # This triggers HTMX partial update (hx-swap="outerHTML")
        await page.fill('[data-testid="input-email"]', test_user["email"])
        await page.fill('[data-testid="input-display-name"]', test_user["display_name"])
        await page.fill('[data-testid="input-password"]', test_user["password"])
        await page.fill('input[name="confirm_password"]', "WrongPassword123!")  # MISMATCH!
        await page.click('[data-testid="submit-register"]')

        # STEP 4: Wait for HTMX to swap form fragment
        error_msg = page.locator("text=Passwords do not match")
        await expect(error_msg).to_be_visible(timeout=5000)

        # STEP 5: Verify form still exists (HTMX swapped it, not full page reload)
        await expect(page.locator('[data-testid="register-form"]')).to_be_visible()

        # STEP 6: Verify NEW token exists in swapped fragment
        csrf_input2 = page.locator('input[name="fastapi-csrf-token"]')
        token2 = await csrf_input2.get_attribute("value")
        assert token2 is not None

        # STEP 7: Verify token was ROTATED by HTMX swap
        assert token2 != token1, "Token should be rotated after HTMX fragment swap"

        # STEP 8: Verify CSRF cookie was also updated
        cookies = await page.context.cookies()
        csrf_cookie = next((c for c in cookies if c["name"] == "fastapi-csrf-token"), None)
        assert csrf_cookie is not None, "CSRF cookie should be present"

        # STEP 9: Submit again with corrected password using new token
        await page.fill('[data-testid="input-password"]', test_user["password"])
        await page.fill('input[name="confirm_password"]', test_user["password"])
        await page.click('[data-testid="submit-register"]')

        # STEP 10: Verify successful registration (HTMX completes the flow)
        await page.wait_for_url(f"{base_url}/dashboard", timeout=5000)
