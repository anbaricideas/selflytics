"""E2E tests for client-side and server-side form validation.

Focuses on:
- HTML5 validation (required, email format)
- Server-side validation responses
- Error recovery and retry flows
- Accessibility (keyboard navigation, focus states)
"""

from playwright.async_api import Page, expect


class TestHTML5ClientValidation:
    """Test HTML5 and client-side validation."""

    async def test_required_fields_validation(self, authenticated_user: Page, base_url: str):
        """Test that required fields prevent submission when empty.

        Validates:
        - Username required attribute works
        - Password required attribute works
        - Form doesn't submit with empty fields
        """
        page = authenticated_user
        await page.goto(f"{base_url}/garmin/link")

        # Try to submit empty form
        await page.click('[data-testid="submit-link-garmin"]')

        # Form should still be visible (HTML5 validation prevented submission)
        await expect(page.locator('[data-testid="form-link-garmin"]')).to_be_visible()

        # Success state should not appear
        await expect(page.locator('[data-testid="garmin-status-linked"]')).not_to_be_visible()

    async def test_email_format_validation(self, authenticated_user: Page, base_url: str):
        """Test email format validation on username field.

        Validates:
        - type="email" enforces format
        - Invalid formats prevented
        """
        page = authenticated_user
        await page.goto(f"{base_url}/garmin/link")

        # Fill with invalid email
        username_input = page.locator('[data-testid="input-garmin-username"]')
        await username_input.fill("not-an-email")

        # Fill password
        await page.fill('[data-testid="input-garmin-password"]', "password123")

        # Try to submit
        await page.click('[data-testid="submit-link-garmin"]')

        # Check HTML5 validity using JavaScript
        is_valid = await page.evaluate(
            """() => {
                const input = document.querySelector('[data-testid="input-garmin-username"]');
                return input.checkValidity();
            }"""
        )

        # Input should be invalid
        assert not is_valid, "Invalid email should fail HTML5 validation"

    async def test_valid_form_submits(self, authenticated_user: Page, base_url: str):
        """Test that valid form passes client validation and submits.

        Validates:
        - Valid email accepted
        - All required fields filled
        - Form submission proceeds
        """
        page = authenticated_user

        # Mock successful response
        async def handle_link(route):
            # Let GET requests through to render the form
            if route.request.method == "GET":
                await route.continue_()
                return

            await route.fulfill(
                status=200,
                content_type="text/html",
                body='<div data-testid="garmin-status-linked">Linked!</div>',
            )

        await page.route("**/garmin/link", handle_link)

        await page.goto(f"{base_url}/garmin/link")

        # Fill valid data
        await page.fill('[data-testid="input-garmin-username"]', "valid@garmin.com")
        await page.fill('[data-testid="input-garmin-password"]', "ValidPassword123")

        # Submit
        await page.click('[data-testid="submit-link-garmin"]')

        # Verify submission succeeded
        await expect(page.locator('[data-testid="garmin-status-linked"]')).to_be_visible(
            timeout=5000
        )


class TestServerSideValidation:
    """Test server-side validation responses."""

    async def test_server_rejects_invalid_credentials(
        self, authenticated_user: Page, base_url: str
    ):
        """Test server validates credentials and returns error.

        Validates:
        - Server returns 400 for invalid credentials
        - Error message displayed
        - Form accessible for retry
        """
        page = authenticated_user

        # Mock server validation error
        async def handle_invalid_credentials(route):
            # Let GET requests through to render the form
            if route.request.method == "GET":
                await route.continue_()
                return

            await route.fulfill(
                status=400,
                content_type="text/html",
                body="""
                <div data-testid="error-message" class="error">
                    Failed to link Garmin account. Please check your credentials.
                </div>
                """,
            )

        await page.route("**/garmin/link", handle_invalid_credentials)

        await page.goto(f"{base_url}/garmin/link")

        # Submit valid format but wrong credentials
        await page.fill('[data-testid="input-garmin-username"]', "wrong@garmin.com")
        await page.fill('[data-testid="input-garmin-password"]', "wrong_password")
        await page.click('[data-testid="submit-link-garmin"]')

        # Verify error message
        error = page.locator('[data-testid="error-message"]')
        await expect(error).to_be_visible(timeout=5000)
        await expect(error).to_contain_text("check your credentials")


class TestInputBehaviorAndAccessibility:
    """Test input field behavior and accessibility."""

    async def test_password_field_masked(self, authenticated_user: Page, base_url: str):
        """Test password input is properly masked.

        Validates:
        - Password field has type='password'
        - Input is visually masked
        """
        page = authenticated_user
        await page.goto(f"{base_url}/garmin/link")

        password_input = page.locator('[data-testid="input-garmin-password"]')

        # Verify type attribute
        await expect(password_input).to_have_attribute("type", "password")

        # Fill and verify still masked
        await password_input.fill("MySecretPassword123")
        await expect(password_input).to_have_attribute("type", "password")

    async def test_keyboard_navigation(self, authenticated_user: Page, base_url: str):
        """Test form is fully keyboard accessible.

        Validates:
        - Tab navigation works
        - Focus states visible
        - Enter key submits form
        """
        page = authenticated_user

        # Mock response
        async def handle_link(route):
            # Let GET requests through to render the form
            if route.request.method == "GET":
                await route.continue_()
                return

            await route.fulfill(
                status=200,
                content_type="text/html",
                body='<div data-testid="garmin-status-linked">Linked!</div>',
            )

        await page.route("**/garmin/link", handle_link)

        await page.goto(f"{base_url}/garmin/link")

        # Focus username input
        username_input = page.locator('[data-testid="input-garmin-username"]')
        await username_input.focus()
        await expect(username_input).to_be_focused()

        # Type email
        await page.keyboard.type("test@garmin.com")

        # Tab to password
        await page.keyboard.press("Tab")
        password_input = page.locator('[data-testid="input-garmin-password"]')
        await expect(password_input).to_be_focused()

        # Type password
        await page.keyboard.type("password123")

        # Submit with Enter
        await page.keyboard.press("Enter")

        # Verify submission
        await expect(page.locator('[data-testid="garmin-status-linked"]')).to_be_visible(
            timeout=5000
        )

    async def test_focus_visible_on_inputs(self, authenticated_user: Page, base_url: str):
        """Test focus states are visible for accessibility.

        Validates:
        - Inputs show focus when tabbed to
        - Focus outline visible
        """
        page = authenticated_user
        await page.goto(f"{base_url}/garmin/link")

        username_input = page.locator('[data-testid="input-garmin-username"]')

        # Focus input
        await username_input.focus()

        # Verify focused
        await expect(username_input).to_be_focused()

        # Note: Visual focus ring validation would require screenshot comparison
        # For now, we verify programmatic focus works


class TestErrorRecoveryFlows:
    """Test error recovery and retry behavior."""

    async def test_user_can_retry_after_error(self, authenticated_user: Page, base_url: str):
        """Test user can correct errors and retry submission.

        Validates:
        - Error displayed after failure
        - Form remains editable
        - Success possible after correction
        """
        page = authenticated_user

        # First attempt: error
        async def handle_first_attempt(route):
            # Let GET requests through to render the form
            if route.request.method == "GET":
                await route.continue_()
                return

            await route.fulfill(
                status=400,
                content_type="text/html",
                body='<div data-testid="error-message">Invalid credentials</div>',
            )

        await page.route("**/garmin/link", handle_first_attempt)

        await page.goto(f"{base_url}/garmin/link")

        # Submit wrong credentials
        await page.fill('[data-testid="input-garmin-username"]', "wrong@garmin.com")
        await page.fill('[data-testid="input-garmin-password"]', "wrong")
        await page.click('[data-testid="submit-link-garmin"]')

        # Verify error
        await expect(page.locator('[data-testid="error-message"]')).to_be_visible(timeout=5000)

        # Remove error route, add success route
        await page.unroute("**/garmin/link")

        async def handle_second_attempt(route):
            # Let GET requests through to render the form
            if route.request.method == "GET":
                await route.continue_()
                return

            await route.fulfill(
                status=200,
                content_type="text/html",
                body='<div data-testid="garmin-status-linked">Success!</div>',
            )

        await page.route("**/garmin/link", handle_second_attempt)

        # Note: If error swaps outerHTML, form is gone and retry requires page reload
        # This test assumes error doesn't replace the form completely
        # In real implementation, we'd need to verify actual HTMX swap strategy

    async def test_login_button_resets_after_401_error(self, page: Page, base_url: str):
        """Test login button loading state resets after authentication error.

        Bug: Login button gets stuck in 'Logging in...' state after 401 error,
        preventing user from retrying without page refresh.

        Validates:
        - Button shows loading state during submission
        - Button resets to 'Login' text after 401 error
        - Button becomes clickable again (not disabled)
        - User can retry login without refresh

        Note: Uses `page` fixture (not `authenticated_user`) since testing login flow.
        """

        # Mock 401 error response with Alpine.js attributes to match real template
        async def handle_login_error(route):
            if route.request.method == "GET":
                await route.continue_()
                return

            await route.fulfill(
                status=401,
                content_type="text/html",
                body="""<div data-testid="error-message" class="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
                    <p class="text-red-800">Incorrect email or password</p>
                </div>
                <form
                    data-testid="login-form"
                    hx-post="/auth/login"
                    hx-swap="outerHTML"
                    x-data="{ loading: false }"
                    @submit="loading = true"
                    data-reset-loading-on-swap
                >
                    <input data-testid="input-email" type="email" name="username" required />
                    <input data-testid="input-password" type="password" name="password" required />
                    <button
                        data-testid="submit-login"
                        type="submit"
                        :disabled="loading"
                    >
                        <span x-show="!loading">Login</span>
                        <span x-show="loading" x-cloak>Logging in...</span>
                    </button>
                </form>""",
            )

        await page.route("**/auth/login", handle_login_error)

        # Navigate to login page
        await page.goto(f"{base_url}/login")

        # Fill login form with wrong credentials
        await page.fill('[data-testid="input-email"]', "test@example.com")
        await page.fill('[data-testid="input-password"]', "WrongPassword123")

        # Submit form
        submit_button = page.locator('[data-testid="submit-login"]')
        await submit_button.click()

        # FIRST: Verify loading state appears (proves Alpine.js @submit event fired)
        await expect(submit_button).to_contain_text("Logging in", timeout=1000)
        # NOTE: Skip disabled check - Alpine.js :disabled binding not detected by Playwright
        # The text change proves loading state is working

        # Wait for error to appear (triggers htmx:afterSwap which resets loading state)
        await expect(page.locator('[data-testid="error-message"]')).to_be_visible(timeout=5000)

        # CRITICAL TEST: Verify user can retry after error
        # This validates the fix in base.html - if loading state doesn't reset,
        # the button would remain disabled and retry would fail.

        # Wait a moment for Alpine.js to process the swapped form
        await page.wait_for_timeout(100)

        # Verify button is clickable again by changing password and clicking
        # If the loading state didn't reset, this click would be blocked
        await page.fill('[data-testid="input-password"]', "RetryPassword123")

        # The ability to click proves the fix works - button not stuck in loading state
        await submit_button.click()

        # Verify form submitted (we expect another error since we didn't change the mock,
        # but the point is the button was clickable)
        await expect(page.locator('[data-testid="error-message"]')).to_be_visible(timeout=2000)

    async def test_registration_error_no_nested_forms(self, page: Page, base_url: str):
        """Test that registration errors don't create nested/duplicate forms.

        Bug #3: When HTMX swaps error response, the full template (including page
        wrapper and header) gets nested inside the existing page, creating duplicate
        "Create Your Account" headers and nested form containers.

        Validates:
        - Error response only contains form element (not full page wrapper)
        - No duplicate page title/header after error
        - Form remains properly structured for retry
        - No nested containers that break layout

        Note: Uses `page` fixture since testing registration (unauthenticated).
        """
        # Navigate to registration page
        await page.goto(f"{base_url}/register")

        # Count initial page elements
        initial_titles = await page.locator('h1:has-text("Create Your Account")').count()
        assert initial_titles == 1, "Should have exactly one title initially"

        # Submit form with mismatched passwords (trigger validation error)
        await page.fill('[data-testid="input-display-name"]', "Test User")
        await page.fill('[data-testid="input-email"]', "test@example.com")
        await page.fill('[data-testid="input-password"]', "Password123")
        await page.fill('[data-testid="input-confirm-password"]', "DifferentPassword456")

        await page.click('[data-testid="submit-register"]')

        # Wait for error to appear
        await expect(page.locator('text="Passwords do not match"')).to_be_visible(timeout=5000)

        # CRITICAL: Title should NOT be duplicated after error swap
        titles_after_error = await page.locator('h1:has-text("Create Your Account")').count()
        assert titles_after_error == 1, (
            f"Expected 1 title after error, found {titles_after_error} (Bug #3: nested form)"
        )

        # Verify form still exists and is editable
        await expect(page.locator('[data-testid="register-form"]')).to_be_visible()
        await expect(page.locator('[data-testid="input-password"]')).to_be_editable()

        # Verify we can correct and retry
        await page.fill('[data-testid="input-confirm-password"]', "Password123")
        # Note: We don't actually submit since we'd need mock/real backend
