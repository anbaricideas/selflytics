"""Debug script to understand route handler behavior with authenticated_user fixture.

Created: 2025-11-14
Purpose: Investigate why inline route handlers cause GET requests to hang
"""
import asyncio
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "backend"))

from playwright.async_api import async_playwright


async def test_inline_handler_blocks_get():
    """Test: inline route handler blocks GET requests."""
    print("\n=== Test 1: Inline handler WITHOUT GET handling ===")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        # Set up inline handler (like failing tests do)
        def handle_link(route):
            print(f"Route intercepted: {route.request.method} {route.request.url}")
            if route.request.method == "POST":
                route.fulfill(
                    status=200,
                    content_type="text/html",
                    body='<div data-testid="garmin-status-linked">Success!</div>',
                )
            # BUG: No handling for GET - will hang!

        await page.route("**/garmin/link", handle_link)

        print("Navigating to /garmin/link with inline handler...")
        try:
            await page.goto("http://localhost:8042/garmin/link", timeout=5000)
            html = await page.content()
            print(f"Page loaded! HTML length: {len(html)}")
            print(f"Form present: {'input-garmin-username' in html}")
        except Exception as e:
            print(f"ERROR: {type(e).__name__}: {e}")

        await browser.close()


async def test_mock_garmin_api_pattern():
    """Test: mock_garmin_api pattern with GET passthrough."""
    print("\n=== Test 2: Mock pattern WITH GET handling ===")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        # Set up handler like mock_garmin_api does
        def handle_link(route):
            print(f"Route intercepted: {route.request.method} {route.request.url}")
            if route.request.method == "GET":
                print("GET request - passing through to backend")
                route.continue_()
                return

            # Handle POST
            if route.request.method == "POST":
                route.fulfill(
                    status=200,
                    content_type="text/html",
                    body='<div data-testid="garmin-status-linked">Success!</div>',
                )

        await page.route("**/garmin/link", handle_link)

        print("Navigating to /garmin/link with GET passthrough...")
        try:
            await page.goto("http://localhost:8042/garmin/link", timeout=5000)
            html = await page.content()
            print(f"Page loaded! HTML length: {len(html)}")
            print(f"Form present: {'input-garmin-username' in html}")

            # Try to find the form
            form = await page.query_selector('[data-testid="form-link-garmin"]')
            print(f"Form found: {form is not None}")
        except Exception as e:
            print(f"ERROR: {type(e).__name__}: {e}")

        await browser.close()


async def main():
    print("Debug: Route handler blocking investigation")
    print("=" * 60)
    print("Hypothesis: Inline handlers without GET handling block page loads")
    print("=" * 60)

    # Test 1: Demonstrates the bug
    await test_inline_handler_blocks_get()

    # Test 2: Shows the fix
    await test_mock_garmin_api_pattern()

    print("\n" + "=" * 60)
    print("CONCLUSION:")
    print("- Inline handlers MUST handle GET requests explicitly")
    print("- Use route.continue_() to pass GET through to backend")
    print("- Or only intercept POST: page.route(..., lambda r: handle(r) if r.request.method == 'POST' else r.continue_())")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
