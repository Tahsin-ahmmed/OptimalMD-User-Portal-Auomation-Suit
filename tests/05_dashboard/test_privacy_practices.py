"""'Privacy Practices' opens its page in a new tab; closing the tab leaves the dashboard."""
import re

from playwright.sync_api import expect


def test_privacy_practices_opens_in_new_tab(dashboard):
    tab = dashboard.click_and_get_new_tab(dashboard.footer_link("Privacy Practices"))
    expect(tab).to_have_url(re.compile(r"optimalmd\.com/privacy-practices"), timeout=60_000)
    print(f"\n  'Privacy Practices' opened a new tab: {tab.url[:80]}")

    tab.close()
    expect(dashboard.care_services_heading, "Dashboard still open after closing the tab").to_be_visible()
    print("  Tab closed -> dashboard")
