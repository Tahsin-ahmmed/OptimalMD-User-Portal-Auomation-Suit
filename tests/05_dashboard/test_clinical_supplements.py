"""'Clinical Grade Supplements' opens its page in a new tab; closing the tab leaves the dashboard."""
import re

from playwright.sync_api import expect


def test_clinical_supplements_opens_in_new_tab(dashboard):
    tab = dashboard.click_and_get_new_tab(dashboard.card_button("supplement", "Get Started"))
    expect(tab).to_have_url(re.compile(r"us\.fullscript\.com/.*optimalmd"), timeout=60_000)
    print(f"\n  'Clinical Grade Supplements' opened a new tab: {tab.url[:80]}")

    tab.close()
    expect(dashboard.care_services_heading, "Dashboard still open after closing the tab").to_be_visible()
    print("  Tab closed -> dashboard")
