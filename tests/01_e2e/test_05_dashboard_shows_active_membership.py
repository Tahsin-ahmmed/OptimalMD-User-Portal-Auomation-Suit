"""E2E step 5: after activation the dashboard shows 100% profile completion and the Prime plan."""
import pytest
from playwright.sync_api import expect

from pages.dashboard_page import DashboardPage
from utils.test_data import PRIME

pytestmark = pytest.mark.e2e
JOURNEY = "new_member"


def test_step5_dashboard_shows_active_membership(journey):
    dashboard = DashboardPage(journey["page"]).wait_until_loaded()

    expect(dashboard.profile_completion(100), "Profile completion 100%").to_be_visible()
    expect(dashboard.current_plan(PRIME), f"Current plan '{PRIME}'").to_be_visible()
    expect(dashboard.member_name(journey["full_name"]), "Member name on dashboard").to_be_visible()
    expect(dashboard.complete_profile_popup, "'Complete your profile' popup should be gone").to_be_hidden()
    print(f"\n  Dashboard: 100% profile complete, plan {PRIME}, member {journey['full_name']}")
