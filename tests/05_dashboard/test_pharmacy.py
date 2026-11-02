"""Nav 'Pharmacy' opens the OptimalRx pharmacy portal; browser Back returns to the dashboard."""
import re

from playwright.sync_api import expect

# SSO goes through omdrx.com/member-login-for-omdrx.php and lands on another omdrx.com page.
PHARMACY_URL = re.compile(r"omdrx\.com/")


def test_pharmacy_opens(dashboard):
    dashboard.nav_link("Pharmacy").click()

    page = dashboard.page
    expect(page, "Pharmacy portal (omdrx.com) opened").to_have_url(PHARMACY_URL, timeout=60_000)
    page.wait_for_load_state("domcontentloaded")
    print(f"\n  'Pharmacy' opened the OptimalRx pharmacy portal | title: {page.title()}")

    dashboard.back_to_dashboard()
    print("  Back -> dashboard")
