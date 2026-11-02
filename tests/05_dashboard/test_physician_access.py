"""Nav 'Physician Access' opens telemedicine, which only serves the USA.

From anywhere else it shows a geo-restriction message, which is what this test
expects. Run from a US location, the message is not shown and this test fails.
"""
import re

from playwright.sync_api import expect

TELEMEDICINE_URL = re.compile(r"mytelemedicine\.com/opmd/login/sso/")
GEO_BLOCK_MESSAGE = "Service not available in your geographical location. Please call Customer Service"


def test_physician_access_shows_geo_restriction(dashboard):
    dashboard.nav_link("Physician Access").click()

    page = dashboard.page
    expect(page, "Telemedicine SSO opened").to_have_url(TELEMEDICINE_URL, timeout=60_000)
    expect(page.get_by_text(GEO_BLOCK_MESSAGE), "Geo-restriction message").to_be_visible(timeout=60_000)
    print(f"\n  'Physician Access' opened telemedicine and shows: '{GEO_BLOCK_MESSAGE}'")

    dashboard.back_to_dashboard()
    print("  Back -> dashboard")
