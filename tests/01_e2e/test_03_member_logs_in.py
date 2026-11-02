"""E2E step 3: the member logs in with the emailed credentials and is asked to complete their profile."""
import pytest
from playwright.sync_api import expect

from pages.dashboard_page import DashboardPage
from pages.login_page import LoginPage

pytestmark = pytest.mark.e2e
JOURNEY = "new_member"


def test_step3_login_with_emailed_credentials(journey):
    credentials = journey["credentials"]
    page = journey["new_page"]()  # fresh browser session, nothing carried over from registration
    LoginPage(page).open().login(credentials["username"], credentials["password"])

    dashboard = DashboardPage(page).wait_until_loaded()
    expect(dashboard.member_name(journey["full_name"]), "Member name on dashboard").to_be_visible()
    expect(dashboard.complete_profile_popup, "'Complete your profile' popup on first login").to_be_visible()
    print(f"\n  Logged in as {journey['full_name']}, 'complete your profile' popup shown")
