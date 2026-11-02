"""'View Imaging' opens /imaging/rates; browser Back returns to the dashboard."""
import re

from playwright.sync_api import expect


def test_view_imaging_opens_its_page(dashboard):
    dashboard.card_button("imaging", "View Imaging").click()

    page = dashboard.page
    expect(page).to_have_url(re.compile(re.escape("/imaging/rates")))
    expect(page.locator("main")).to_contain_text("FACILITY LOCATIONS AND RATES", ignore_case=True)
    print(f"\n  'View Imaging' opened {page.url}")

    dashboard.back_to_dashboard()
    print("  Back -> dashboard")
