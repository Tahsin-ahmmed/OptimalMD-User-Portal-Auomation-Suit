"""'University' opens /training; browser Back returns to the dashboard."""
import re

from playwright.sync_api import expect


def test_university_opens_its_page(dashboard):
    dashboard.nav_link("University").click()

    page = dashboard.page
    expect(page).to_have_url(re.compile(re.escape("/training")))
    expect(page.locator("main")).to_contain_text("Documents", ignore_case=True)
    print(f"\n  'University' opened {page.url}")

    dashboard.back_to_dashboard()
    print("  Back -> dashboard")
