"""
Debug script for e2e test failure with HTMX form swap.
Created: 2025-11-14
Purpose: Investigate why [data-testid="garmin-status-linked"] is not appearing after form submission.

This script instruments the failing test to capture:
1. Network requests (especially POST to /garmin/link)
2. Page content before/after form submission
3. Console logs and HTMX events
4. Mock route invocation details
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path for imports
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))


def debug_test():
    """Run instrumented version of failing test."""
    import time
    import uuid
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=500)
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            ignore_https_errors=True,
        )
        page = context.new_page()

        # Enable verbose console logging
        page.on("console", lambda msg: print(f"[BROWSER CONSOLE] {msg.type}: {msg.text}"))
        page.on("pageerror", lambda exc: print(f"[BROWSER ERROR] {exc}"))

        # Track network requests
        requests = []
        responses = []

        def log_request(request):
            print(f"[NETWORK REQUEST] {request.method} {request.url}")
            if request.method == "POST":
                print(f"  POST DATA: {request.post_data}")
                print(f"  HEADERS: {dict(request.headers)}")
            requests.append(request)

        def log_response(response):
            print(f"[NETWORK RESPONSE] {response.status} {response.url}")
            if response.url.endswith("/garmin/link") and response.request.method == "POST":
                print(f"  CONTENT-TYPE: {response.headers.get('content-type')}")
                print(f"  BODY (first 500 chars): {response.text()[:500]}")
            responses.append(response)

        page.on("request", log_request)
        page.on("response", log_response)

        # Setup mock routes
        mock_call_count = {"link": 0, "sync": 0}

        def handle_garmin_link(route):
            """Mock Garmin link endpoint with detailed logging."""
            request = route.request
            mock_call_count["link"] += 1

            print(f"\n[MOCK CALLED] handle_garmin_link (call #{mock_call_count['link']})")
            print(f"  METHOD: {request.method}")
            print(f"  URL: {request.url}")
            print(f"  HEADERS: {dict(request.headers)}")

            # Let GET requests through
            if request.method == "GET":
                print("  ACTION: Passing through to backend (GET request)")
                route.continue_()
                return

            # Handle POST
            post_data = request.post_data
            print(f"  POST DATA TYPE: {type(post_data)}")
            print(f"  POST DATA: {post_data}")

            # Check for test@garmin.com
            has_test_email = (
                (isinstance(post_data, bytes) and b"test@garmin.com" in post_data)
                or (isinstance(post_data, str) and "test@garmin.com" in post_data)
            )
            print(f"  HAS TEST EMAIL: {has_test_email}")

            if post_data and has_test_email:
                print("  ACTION: Returning success HTML fragment")
                html_response = """
                <div data-testid="garmin-status-linked" class="bg-green-50 border border-green-200 rounded-lg p-6">
                    <p class="text-green-800 font-semibold">Garmin account linked</p>
                    <button
                        data-testid="button-sync-garmin"
                        hx-post="/garmin/sync"
                        hx-swap="outerHTML"
                        class="mt-4 px-4 py-2 bg-blue-600 text-white rounded-md"
                    >
                        Sync Now
                    </button>
                </div>
                """
                route.fulfill(
                    status=200,
                    content_type="text/html",
                    body=html_response,
                )
                print(f"  HTML LENGTH: {len(html_response)} chars")
            else:
                print("  ACTION: Returning error (invalid credentials)")
                route.fulfill(
                    status=400,
                    content_type="text/html",
                    body='<div class="error" data-testid="error-message">Failed to link Garmin account. Invalid credentials.</div>',
                )

        def handle_garmin_sync(route):
            """Mock Garmin sync endpoint."""
            mock_call_count["sync"] += 1
            print(f"\n[MOCK CALLED] handle_garmin_sync (call #{mock_call_count['sync']})")
            route.fulfill(
                status=200,
                content_type="text/html",
                body='<div data-testid="sync-success" class="text-green-600">Sync completed successfully</div>',
            )

        page.route("**/garmin/link", handle_garmin_link)
        page.route("**/garmin/sync", handle_garmin_sync)

        # Generate test user
        timestamp = int(time.time())
        test_id = uuid.uuid4().hex[:6]
        test_user = {
            "email": f"e2e-debug-{test_id}-{timestamp}@example.com",
            "password": "TestPass123!",
            "display_name": f"Debug User {test_id}",
        }

        base_url = "http://localhost:8042"

        print("\n=== STARTING TEST ===\n")

        # Step 1: Register user
        print("[STEP 1] Navigating to registration")
        page.goto(base_url)
        page.click('[data-testid="register-link"]')
        page.wait_for_selector('[data-testid="register-form"]', state="visible")

        print("[STEP 1] Filling registration form")
        page.fill('[data-testid="input-display-name"]', test_user["display_name"])
        page.fill('[data-testid="input-email"]', test_user["email"])
        page.fill('[data-testid="input-password"]', test_user["password"])
        page.fill('input[name="confirm_password"]', test_user["password"])
        page.click('[data-testid="submit-register"]')

        print("[STEP 1] Waiting for redirect to dashboard")
        page.wait_for_url(f"{base_url}/dashboard", timeout=10000)
        print(f"[STEP 1] Current URL: {page.url}")

        # Step 2: Navigate to Garmin link page
        print("\n[STEP 2] Navigating to /garmin/link")
        page.goto(f"{base_url}/garmin/link")
        page.wait_for_load_state("networkidle")
        print(f"[STEP 2] Page loaded, URL: {page.url}")

        # Verify form is visible
        form = page.locator('[data-testid="form-link-garmin"]')
        print(f"[STEP 2] Form visible: {form.is_visible()}")

        # Check HTMX is loaded
        htmx_loaded = page.evaluate("typeof htmx !== 'undefined'")
        print(f"[STEP 2] HTMX loaded: {htmx_loaded}")

        if htmx_loaded:
            htmx_version = page.evaluate("htmx.version")
            print(f"[STEP 2] HTMX version: {htmx_version}")

        # Capture page content before submission
        print("\n[STEP 3] Capturing page content BEFORE form submission")
        content_before = page.content()
        print(f"[STEP 3] Page content length: {len(content_before)} chars")
        print(f"[STEP 3] Contains form-link-garmin: {'form-link-garmin' in content_before}")
        print(f"[STEP 3] Contains garmin-status-linked: {'garmin-status-linked' in content_before}")

        # Fill form
        print("\n[STEP 4] Filling Garmin credentials")
        page.fill('[data-testid="input-garmin-username"]', "test@garmin.com")
        page.fill('[data-testid="input-garmin-password"]', "password123")

        # Check form values
        username_value = page.input_value('[data-testid="input-garmin-username"]')
        password_value = page.input_value('[data-testid="input-garmin-password"]')
        print(f"[STEP 4] Username field value: {username_value}")
        print(f"[STEP 4] Password field value: {'*' * len(password_value)}")

        # Submit form
        print("\n[STEP 5] Clicking submit button")
        submit_button = page.locator('[data-testid="submit-link-garmin"]')
        print(f"[STEP 5] Submit button visible: {submit_button.is_visible()}")
        print(f"[STEP 5] Submit button enabled: {submit_button.is_enabled()}")

        # Click and wait a moment
        submit_button.click()
        print("[STEP 5] Clicked submit button")

        # Wait for network activity to settle
        print("[STEP 5] Waiting for network idle (2 seconds)")
        page.wait_for_load_state("networkidle", timeout=5000)

        # Capture page content after submission
        print("\n[STEP 6] Capturing page content AFTER form submission")
        content_after = page.content()
        print(f"[STEP 6] Page content length: {len(content_after)} chars")
        print(f"[STEP 6] Contains form-link-garmin: {'form-link-garmin' in content_after}")
        print(f"[STEP 6] Contains garmin-status-linked: {'garmin-status-linked' in content_after}")

        # Check if target element exists
        target = page.locator('[data-testid="garmin-status-linked"]')
        target_visible = target.is_visible() if target.count() > 0 else False
        print(f"[STEP 6] Target element count: {target.count()}")
        print(f"[STEP 6] Target visible: {target_visible}")

        # Save screenshots
        screenshots_dir = Path(__file__).parent.parent / "scripts" / "debug_screenshots"
        screenshots_dir.mkdir(exist_ok=True)
        page.screenshot(path=str(screenshots_dir / "after_submit.png"))
        print(f"[STEP 6] Screenshot saved to {screenshots_dir / 'after_submit.png'}")

        # Summary
        print("\n=== SUMMARY ===")
        print(f"Total requests: {len(requests)}")
        print(f"Total responses: {len(responses)}")
        print(f"Mock 'link' called: {mock_call_count['link']} times")
        print(f"Mock 'sync' called: {mock_call_count['sync']} times")

        # Check for POST to /garmin/link
        post_requests = [r for r in requests if r.method == "POST" and "garmin/link" in r.url]
        print(f"POST requests to /garmin/link: {len(post_requests)}")

        if post_requests:
            for i, req in enumerate(post_requests):
                print(f"  POST #{i+1}: {req.url}")
                print(f"    POST DATA: {req.post_data}")

        # Print content diff (first 1000 chars)
        print("\n=== CONTENT CHANGES ===")
        if content_before == content_after:
            print("NO CHANGES - Content identical before and after submission")
        else:
            print("Content changed")
            # Find where form tag is in both
            form_before_idx = content_before.find('data-testid="form-link-garmin"')
            form_after_idx = content_after.find('data-testid="form-link-garmin"')
            status_after_idx = content_after.find('data-testid="garmin-status-linked"')

            print(f"  Form exists BEFORE: {form_before_idx != -1} (index: {form_before_idx})")
            print(f"  Form exists AFTER: {form_after_idx != -1} (index: {form_after_idx})")
            print(f"  Status exists AFTER: {status_after_idx != -1} (index: {status_after_idx})")

        print("\n[DEBUG] Waiting 10 seconds before closing (inspect browser)")
        time.sleep(10)

        browser.close()


if __name__ == "__main__":
    debug_test()
