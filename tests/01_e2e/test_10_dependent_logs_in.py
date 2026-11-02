"""E2E step 10: the dependent logs in with their emailed credentials; their profile is already complete."""
import pytest
from playwright.sync_api import expect

from pages.dashboard_page import DashboardPage
from pages.login_page import LoginPage
from utils.test_data import PRIME

pytestmark = pytest.mark.e2e
JOURNEY = "new_member"


def test_step10_dependent_logs_in(journey):
    credentials = journey["dependent_credentials"]
    page = journey["page"]
    LoginPage(page).login(credentials["username"], credentials["password"])

    dashboard = DashboardPage(page).wait_until_loaded()
    name = journey["dependent_name"]
    # The member already activated this dependent, so their profile is complete on first login.
    expect(dashboard.member_name(name), "Dependent's name on dashboard").to_be_visible()
    expect(dashboard.profile_completion(100), "Dependent profile completion 100%").to_be_visible()
    expect(dashboard.current_plan(PRIME), f"Dependent's plan '{PRIME}'").to_be_visible()
    expect(dashboard.complete_profile_popup, "No 'complete your profile' popup").to_be_hidden()
    print(f"\n  Logged in as dependent {name}: 100% complete, plan {PRIME}")
