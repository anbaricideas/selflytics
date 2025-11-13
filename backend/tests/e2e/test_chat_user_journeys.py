"""E2E User Journey Tests: Complete chat workflows using Playwright.

These tests verify the full user experience from login through chat interaction.
Requires running server with mocked external APIs.
"""

import pytest
from playwright.sync_api import Page, expect


@pytest.mark.skip(reason="E2E tests require running server - implement in future session")
def test_complete_chat_journey_e2e(page: Page, base_url):
    """Test: Full user journey from login to chat interaction."""
    # Mock external APIs at network level
    page.route(
        "**/api.openai.com/**",
        lambda route: route.fulfill(
            json={
                "choices": [
                    {
                        "message": {
                            "content": "You ran 5 times this week!",
                            "role": "assistant",
                        }
                    }
                ],
                "usage": {"prompt_tokens": 100, "completion_tokens": 50},
            }
        ),
    )

    page.route(
        "**/garmin.com/**",
        lambda route: route.fulfill(
            json={
                "activities": [
                    {"distance": 5000, "duration": 1800, "type": "running"} for _ in range(5)
                ]
            }
        ),
    )

    # 1. User logs in
    page.goto(f"{base_url}/login")
    page.fill("#email", "test@example.com")
    page.fill("#password", "password123")
    page.click("button[type=submit]")

    # 2. Navigate to chat
    page.wait_for_url(f"{base_url}/dashboard")
    page.click("a[href='/chat']")

    # 3. Send message
    page.wait_for_selector("#messages")
    page.fill("input[placeholder*='fitness data']", "How am I doing this week?")
    page.click("button[type=submit]")

    # 4. Wait for AI response
    expect(page.locator(".animate-pulse")).to_be_visible()  # Loading indicator
    expect(page.locator("text='You ran 5 times'")).to_be_visible(timeout=5000)

    # 5. Verify response displayed
    messages = page.locator(".inline-block.px-4.py-3")
    expect(messages).to_have_count(2)  # User message + AI response

    # 6. Verify conversation saved
    conversations = page.locator("aside .p-3.rounded")
    expect(conversations).to_have_count(1)
    expect(conversations.first).to_contain_text("How am I doing")

    # 7. Send follow-up message
    page.fill("input[placeholder*='fitness data']", "What about my sleep?")
    page.click("button[type=submit]")

    # 8. Verify context retained
    expect(page.locator("text='sleep'")).to_be_visible(timeout=5000)
    expect(messages).to_have_count(4)  # 2 user + 2 AI messages


@pytest.mark.skip(reason="E2E tests require running server - implement in future session")
def test_new_conversation_button(page: Page, base_url):
    """Test: New conversation button clears chat and starts fresh."""
    page.goto(f"{base_url}/chat")

    # Send initial message
    page.fill("input[placeholder*='fitness data']", "Test message")
    page.click("button[type=submit]")
    page.wait_for_selector(".inline-block.px-4.py-3")

    # Click "New Chat" button
    page.click("button:has-text('New Chat')")

    # Verify chat cleared
    messages = page.locator(".inline-block.px-4.py-3")
    expect(messages).to_have_count(0)

    # Verify input empty
    input_field = page.locator("input[placeholder*='fitness data']")
    expect(input_field).to_have_value("")


@pytest.mark.skip(reason="E2E tests require running server - implement in future session")
def test_conversation_list_navigation(page: Page, base_url):
    """Test: Click conversation in sidebar to load message history."""
    page.goto(f"{base_url}/chat")

    # Create first conversation
    page.fill("input[placeholder*='fitness data']", "First conversation")
    page.click("button[type=submit]")
    page.wait_for_selector("aside .p-3.rounded")

    # Create second conversation
    page.click("button:has-text('New Chat')")
    page.fill("input[placeholder*='fitness data']", "Second conversation")
    page.click("button[type=submit]")

    # Verify 2 conversations in sidebar
    conversations = page.locator("aside .p-3.rounded")
    expect(conversations).to_have_count(2)

    # Click first conversation
    conversations.first.click()

    # Verify first conversation loaded
    expect(page.locator("text='First conversation'")).to_be_visible()


@pytest.mark.skip(reason="E2E tests require running server - implement in future session")
def test_error_handling_display(page: Page, base_url):
    """Test: Error messages displayed properly to user."""
    # Mock API to return error
    page.route(
        "**/chat/send",
        lambda route: route.fulfill(status=500, json={"detail": "API Error"}),
    )

    page.goto(f"{base_url}/chat")
    page.fill("input[placeholder*='fitness data']", "Test message")
    page.click("button[type=submit]")

    # Verify error message displayed
    expect(page.locator(".bg-red-100")).to_be_visible()
    expect(page.locator("text='API Error'")).to_be_visible()

    # Verify message restored to input
    input_field = page.locator("input[placeholder*='fitness data']")
    expect(input_field).to_have_value("Test message")


@pytest.mark.skip(reason="E2E tests require running server - implement in future session")
def test_loading_state_during_ai_response(page: Page, base_url):
    """Test: Loading indicator shown while waiting for AI response."""
    # Mock slow API response
    page.route(
        "**/chat/send",
        lambda route: page.wait_for_timeout(2000).then(
            lambda: route.fulfill(
                json={
                    "conversation_id": "test",
                    "response": {
                        "message": "Response",
                        "confidence": 0.9,
                        "data_sources_used": [],
                    },
                }
            )
        ),
    )

    page.goto(f"{base_url}/chat")
    page.fill("input[placeholder*='fitness data']", "Test message")
    page.click("button[type=submit]")

    # Verify loading indicator visible
    expect(page.locator(".animate-pulse")).to_be_visible()
    expect(page.locator("text='AI is thinking'")).to_be_visible()

    # Verify input disabled during loading
    input_field = page.locator("input[placeholder*='fitness data']")
    expect(input_field).to_be_disabled()

    # Wait for response
    page.wait_for_selector("text='Response'")

    # Verify loading indicator hidden
    expect(page.locator(".animate-pulse")).not_to_be_visible()
