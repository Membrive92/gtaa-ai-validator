"""
Another test file with violations using Playwright.
"""

from playwright.sync_api import sync_playwright


def test_search_functionality():
    """
    Test search - uses Playwright directly (VIOLATION).
    """
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        # VIOLATION: Direct Playwright calls in test
        page.goto("https://example.com")
        page.locator("#search-input").fill("test query")
        page.locator("button.search-btn").click()

        # VIOLATION: More direct calls
        results = page.locator(".search-results").count()
        assert results > 0

        browser.close()


def test_filter_search_results():
    """Test filtering search results - also has violations."""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        # VIOLATION: Direct Playwright API usage
        page.goto("https://example.com/search?q=test")
        page.click("#filter-dropdown")
        page.click("text=Price: Low to High")

        # Wait and check
        page.wait_for_selector(".filtered-results")

        # VIOLATION
        first_price = page.locator(".price").first.text_content()
        assert "$" in first_price

        browser.close()
