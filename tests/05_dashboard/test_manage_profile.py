"""'Manage Profile' opens /update-profile; browser Back returns to the dashboard."""
import re

from playwright.sync_api import expect


def test_manage_profile_opens_its_page(dashboard):
    dashboard.nav_link("Manage Profile").click()

    page = dashboard.page
    expect(page).to_have_url(re.compile(re.escape("/update-profile")))
    expect(page.locator("main")).to_contain_text("Personal Demographics", ignore_case=True)
    print(f"\n  'Manage Profile' opened {page.url}")

    dashboard.back_to_dashboard()
    print("  Back -> dashboard")
