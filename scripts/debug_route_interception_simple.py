"""Simple debug script to validate route interception hypothesis.

Created: 2025-11-14
Purpose: Confirm that inline route handlers without GET handling cause hangs
"""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "backend"))

from playwright.sync_api import sync_playwright


def test_scenario_1_failing_pattern():
    """Scenario 1: Inline handler WITHOUT GET handling (FAILS)."""
    print("\n" + "=" * 70)
    print("SCENARIO 1: Inline route handler (failing test pattern)")
    print("=" * 70)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Track all requests
        requests = []

        def track_request(request):
            requests.append(f"{request.method} {request.url}")
            print(f"  📤 Request: {request.method} {request.url}")

        def track_response(response):
            print(
                f"  📥 Response: {response.status} {response.url} ({response.request.method})"
            )

        page.on("request", track_request)
        page.on("response", track_response)

        # Inline handler WITHOUT GET handling (LIKE FAILING TESTS)
        def handle_link(route):
            method = route.request.method
            print(f"  🔀 Route handler called: {method}")

            if method == "POST":
                print(f"  ✅ Handling POST with mock response")
                route.fulfill(
                    status=200,
                    content_type="text/html",
                    body='<div data-testid="garmin-status-linked">Success!</div>',
                )
            # BUG: GET requests fall through without handling!
            # route.continue_() is NEVER called for GET
            print(f"  ❌ No handler for GET - request will hang!")

        page.route("**/garmin/link", handle_link)

        print("\n  Navigating to /garmin/link...")
        try:
            page.goto("http://localhost:8042/garmin/link", timeout=5000)
            html = page.content()
            print(f"\n  ✅ SUCCESS: Page loaded ({len(html)} bytes)")
            form_present = "input-garmin-username" in html
            print(f"  Form present: {form_present}")
        except Exception as e:
            print(f"\n  ❌ TIMEOUT: {e}")
            print(f"\n  Requests made: {requests}")

        browser.close()


def test_scenario_2_working_pattern():
    """Scenario 2: Handler WITH GET passthrough (WORKS)."""
    print("\n" + "=" * 70)
    print("SCENARIO 2: mock_garmin_api fixture pattern (working)")
    print("=" * 70)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Track all requests
        requests = []

        def track_request(request):
            requests.append(f"{request.method} {request.url}")
            print(f"  📤 Request: {request.method} {request.url}")

        def track_response(response):
            print(
                f"  📥 Response: {response.status} {response.url} ({response.request.method})"
            )

        page.on("request", track_request)
        page.on("response", track_response)

        # Handler WITH GET passthrough (LIKE mock_garmin_api)
        def handle_link(route):
            method = route.request.method
            print(f"  🔀 Route handler called: {method}")

            if method == "GET":
                print(f"  ✅ Passing GET through to backend")
                route.continue_()
                return

            if method == "POST":
                print(f"  ✅ Handling POST with mock response")
                route.fulfill(
                    status=200,
                    content_type="text/html",
                    body='<div data-testid="garmin-status-linked">Success!</div>',
                )

        page.route("**/garmin/link", handle_link)

        print("\n  Navigating to /garmin/link...")
        try:
            page.goto("http://localhost:8042/garmin/link", timeout=5000)
            html = page.content()
            print(f"\n  ✅ SUCCESS: Page loaded ({len(html)} bytes)")
            form_present = "input-garmin-username" in html
            print(f"  Form present: {form_present}")
        except Exception as e:
            print(f"\n  ❌ TIMEOUT: {e}")
            print(f"\n  Requests made: {requests}")

        browser.close()


def main():
    print("\n" + "=" * 70)
    print("DEBUG: Route Handler Blocking Investigation")
    print("=" * 70)
    print("\nHypothesis: Inline handlers without GET handling block page loads")
    print("because route.continue_() is never called for GET requests.")

    # Test failing pattern
    test_scenario_1_failing_pattern()

    # Test working pattern
    test_scenario_2_working_pattern()

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(
        """
Root Cause: When tests define inline route handlers using page.route(),
they intercept ALL requests to that URL (GET and POST). If the handler
doesn't explicitly call route.continue_() for GET requests, the GET request
hangs indefinitely, preventing the form from rendering.

The mock_garmin_api fixture works because it explicitly checks request.method
and calls route.continue_() for GET requests (lines 126-128 in conftest.py).

Fix: All inline handlers must handle GET requests by calling route.continue_().
"""
    )


if __name__ == "__main__":
    main()
