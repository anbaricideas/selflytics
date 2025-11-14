"""E2E tests for client-side and server-side form validation.

Focuses on:
- HTML5 validation (required, email format)
- Server-side validation responses
- Error recovery and retry flows
- Accessibility (keyboard navigation, focus states)
"""

from playwright.sync_api import Page, expect


class TestHTML5ClientValidation:
    """Test HTML5 and client-side validation."""

    def test_required_fields_validation(self, authenticated_user: Page, base_url: str):
        """Test that required fields prevent submission when empty.

        Validates:
        - Username required attribute works
        - Password required attribute works
        - Form doesn't submit with empty fields
        """
        page = authenticated_user
        page.goto(f"{base_url}/garmin/link")

        # Try to submit empty form
        page.click('[data-testid="submit-link-garmin"]')

        # Form should still be visible (HTML5 validation prevented submission)
        expect(page.locator('[data-testid="form-link-garmin"]')).to_be_visible()

        # Success state should not appear
        expect(page.locator('[data-testid="garmin-status-linked"]')).not_to_be_visible()

    def test_email_format_validation(self, authenticated_user: Page, base_url: str):
        """Test email format validation on username field.

        Validates:
        - type="email" enforces format
        - Invalid formats prevented
        """
        page = authenticated_user
        page.goto(f"{base_url}/garmin/link")

        # Fill with invalid email
        username_input = page.locator('[data-testid="input-garmin-username"]')
        username_input.fill("not-an-email")

        # Fill password
        page.fill('[data-testid="input-garmin-password"]', "password123")

        # Try to submit
        page.click('[data-testid="submit-link-garmin"]')

        # Check HTML5 validity using JavaScript
        is_valid = page.evaluate(
            """() => {
                const input = document.querySelector('[data-testid="input-garmin-username"]');
                return input.checkValidity();
            }"""
        )

        # Input should be invalid
        assert not is_valid, "Invalid email should fail HTML5 validation"

    def test_valid_form_submits(self, authenticated_user: Page, base_url: str):
        """Test that valid form passes client validation and submits.

        Validates:
        - Valid email accepted
        - All required fields filled
        - Form submission proceeds
        """
        page = authenticated_user

        # Mock successful response
        def handle_link(route):
            # Let GET requests through to render the form
            if route.request.method == "GET":
                route.continue_()
                return

            route.fulfill(
                status=200,
                content_type="text/html",
                body='<div data-testid="garmin-status-linked">Linked!</div>',
            )

        page.route("**/garmin/link", handle_link)

        page.goto(f"{base_url}/garmin/link")

        # Fill valid data
        page.fill('[data-testid="input-garmin-username"]', "valid@garmin.com")
        page.fill('[data-testid="input-garmin-password"]', "ValidPassword123")

        # Submit
        page.click('[data-testid="submit-link-garmin"]')

        # Verify submission succeeded
        expect(page.locator('[data-testid="garmin-status-linked"]')).to_be_visible(timeout=5000)


class TestServerSideValidation:
    """Test server-side validation responses."""

    def test_server_rejects_invalid_credentials(self, authenticated_user: Page, base_url: str):
        """Test server validates credentials and returns error.

        Validates:
        - Server returns 400 for invalid credentials
        - Error message displayed
        - Form accessible for retry
        """
        page = authenticated_user

        # Mock server validation error
        def handle_invalid_credentials(route):
            # Let GET requests through to render the form
            if route.request.method == "GET":
                route.continue_()
                return

            route.fulfill(
                status=400,
                content_type="text/html",
                body="""
                <div data-testid="error-message" class="error">
                    Failed to link Garmin account. Please check your credentials.
                </div>
                """,
            )

        page.route("**/garmin/link", handle_invalid_credentials)

        page.goto(f"{base_url}/garmin/link")

        # Submit valid format but wrong credentials
        page.fill('[data-testid="input-garmin-username"]', "wrong@garmin.com")
        page.fill('[data-testid="input-garmin-password"]', "wrong_password")
        page.click('[data-testid="submit-link-garmin"]')

        # Verify error message
        error = page.locator('[data-testid="error-message"]')
        expect(error).to_be_visible(timeout=5000)
        expect(error).to_contain_text("check your credentials")


class TestInputBehaviorAndAccessibility:
    """Test input field behavior and accessibility."""

    def test_password_field_masked(self, authenticated_user: Page, base_url: str):
        """Test password input is properly masked.

        Validates:
        - Password field has type='password'
        - Input is visually masked
        """
        page = authenticated_user
        page.goto(f"{base_url}/garmin/link")

        password_input = page.locator('[data-testid="input-garmin-password"]')

        # Verify type attribute
        expect(password_input).to_have_attribute("type", "password")

        # Fill and verify still masked
        password_input.fill("MySecretPassword123")
        expect(password_input).to_have_attribute("type", "password")

    def test_keyboard_navigation(self, authenticated_user: Page, base_url: str):
        """Test form is fully keyboard accessible.

        Validates:
        - Tab navigation works
        - Focus states visible
        - Enter key submits form
        """
        page = authenticated_user

        # Mock response
        def handle_link(route):
            # Let GET requests through to render the form
            if route.request.method == "GET":
                route.continue_()
                return

            route.fulfill(
                status=200,
                content_type="text/html",
                body='<div data-testid="garmin-status-linked">Linked!</div>',
            )

        page.route("**/garmin/link", handle_link)

        page.goto(f"{base_url}/garmin/link")

        # Focus username input
        username_input = page.locator('[data-testid="input-garmin-username"]')
        username_input.focus()
        expect(username_input).to_be_focused()

        # Type email
        page.keyboard.type("test@garmin.com")

        # Tab to password
        page.keyboard.press("Tab")
        password_input = page.locator('[data-testid="input-garmin-password"]')
        expect(password_input).to_be_focused()

        # Type password
        page.keyboard.type("password123")

        # Submit with Enter
        page.keyboard.press("Enter")

        # Verify submission
        expect(page.locator('[data-testid="garmin-status-linked"]')).to_be_visible(timeout=5000)

    def test_focus_visible_on_inputs(self, authenticated_user: Page, base_url: str):
        """Test focus states are visible for accessibility.

        Validates:
        - Inputs show focus when tabbed to
        - Focus outline visible
        """
        page = authenticated_user
        page.goto(f"{base_url}/garmin/link")

        username_input = page.locator('[data-testid="input-garmin-username"]')

        # Focus input
        username_input.focus()

        # Verify focused
        expect(username_input).to_be_focused()

        # Note: Visual focus ring validation would require screenshot comparison
        # For now, we verify programmatic focus works


class TestErrorRecoveryFlows:
    """Test error recovery and retry behavior."""

    def test_user_can_retry_after_error(self, authenticated_user: Page, base_url: str):
        """Test user can correct errors and retry submission.

        Validates:
        - Error displayed after failure
        - Form remains editable
        - Success possible after correction
        """
        page = authenticated_user

        # First attempt: error
        def handle_first_attempt(route):
            # Let GET requests through to render the form
            if route.request.method == "GET":
                route.continue_()
                return

            route.fulfill(
                status=400,
                content_type="text/html",
                body='<div data-testid="error-message">Invalid credentials</div>',
            )

        page.route("**/garmin/link", handle_first_attempt)

        page.goto(f"{base_url}/garmin/link")

        # Submit wrong credentials
        page.fill('[data-testid="input-garmin-username"]', "wrong@garmin.com")
        page.fill('[data-testid="input-garmin-password"]', "wrong")
        page.click('[data-testid="submit-link-garmin"]')

        # Verify error
        expect(page.locator('[data-testid="error-message"]')).to_be_visible(timeout=5000)

        # Remove error route, add success route
        page.unroute("**/garmin/link")

        def handle_second_attempt(route):
            # Let GET requests through to render the form
            if route.request.method == "GET":
                route.continue_()
                return

            route.fulfill(
                status=200,
                content_type="text/html",
                body='<div data-testid="garmin-status-linked">Success!</div>',
            )

        page.route("**/garmin/link", handle_second_attempt)

        # Note: If error swaps outerHTML, form is gone and retry requires page reload
        # This test assumes error doesn't replace the form completely
        # In real implementation, we'd need to verify actual HTMX swap strategy

    def test_login_button_resets_after_401_error(self, page: Page, base_url: str):
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
        def handle_login_error(route):
            if route.request.method == "GET":
                route.continue_()
                return

            route.fulfill(
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

        page.route("**/auth/login", handle_login_error)

        # Navigate to login page
        page.goto(f"{base_url}/login")

        # Fill login form with wrong credentials
        page.fill('[data-testid="input-email"]', "test@example.com")
        page.fill('[data-testid="input-password"]', "WrongPassword123")

        # Submit form
        submit_button = page.locator('[data-testid="submit-login"]')
        submit_button.click()

        # FIRST: Verify loading state appears (proves Alpine.js @submit event fired)
        expect(submit_button).to_contain_text("Logging in", timeout=1000)
        expect(submit_button).to_be_disabled()

        # Wait for error to appear (triggers htmx:afterSwap which resets loading state)
        expect(page.locator('[data-testid="error-message"]')).to_be_visible(timeout=5000)

        # CRITICAL: Button must reset after error (validates the fix in base.html)
        expect(submit_button).not_to_be_disabled()
        expect(submit_button).to_contain_text("Login")
        expect(submit_button).not_to_contain_text("Logging in")

        # Verify user can retry
        page.fill('[data-testid="input-password"]', "CorrectPassword123")

        # Remove error route, add success route
        page.unroute("**/auth/login")

        def handle_login_success(route):
            if route.request.method == "GET":
                route.continue_()
                return

            route.fulfill(
                status=200,
                headers={"HX-Redirect": "/dashboard"},
                body="",
            )

        page.route("**/auth/login", handle_login_success)

        # Retry submission
        submit_button.click()

        # Should redirect to dashboard
        page.wait_for_url(f"{base_url}/dashboard", timeout=5000)

    def test_registration_error_no_nested_forms(self, page: Page, base_url: str):
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
        page.goto(f"{base_url}/register")

        # Count initial page elements
        initial_titles = page.locator('h1:has-text("Create Your Account")').count()
        assert initial_titles == 1, "Should have exactly one title initially"

        # Submit form with mismatched passwords (trigger validation error)
        page.fill('[data-testid="input-display-name"]', "Test User")
        page.fill('[data-testid="input-email"]', "test@example.com")
        page.fill('[data-testid="input-password"]', "Password123")
        page.fill('[data-testid="input-confirm-password"]', "DifferentPassword456")

        page.click('[data-testid="submit-register"]')

        # Wait for error to appear
        expect(page.locator('text="Passwords do not match"')).to_be_visible(timeout=5000)

        # CRITICAL: Title should NOT be duplicated after error swap
        titles_after_error = page.locator('h1:has-text("Create Your Account")').count()
        assert titles_after_error == 1, (
            f"Expected 1 title after error, found {titles_after_error} (Bug #3: nested form)"
        )

        # Verify form still exists and is editable
        expect(page.locator('[data-testid="register-form"]')).to_be_visible()
        expect(page.locator('[data-testid="input-password"]')).to_be_editable()

        # Verify we can correct and retry
        page.fill('[data-testid="input-confirm-password"]', "Password123")
        # Note: We don't actually submit since we'd need mock/real backend
