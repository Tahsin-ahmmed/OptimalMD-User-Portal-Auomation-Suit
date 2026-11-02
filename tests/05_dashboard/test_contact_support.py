"""'Contact Support' opens /support; browser Back returns to the dashboard."""
import re

from playwright.sync_api import expect


def test_contact_support_opens_its_page(dashboard):
    dashboard.card_button("support", "Contact Support").click()

    page = dashboard.page
    expect(page).to_have_url(re.compile(re.escape("/support")))
    expect(page.locator("main")).to_contain_text("Create Support Ticket", ignore_case=True)
    print(f"\n  'Contact Support' opened {page.url}")

    dashboard.back_to_dashboard()
    print("  Back -> dashboard")
