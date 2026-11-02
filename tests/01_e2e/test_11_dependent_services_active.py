"""E2E step 11: the dependent's My Profile shows the plan, status Active and every service Active."""
import pytest

from pages.dashboard_page import DashboardPage
from pages.my_profile_page import MyProfilePage
from utils.test_data import PRIME

pytestmark = pytest.mark.e2e
JOURNEY = "new_member"


def test_step11_dependent_profile_shows_active_services(journey):
    page = journey["page"]
    DashboardPage(page).open_my_profile()
    MyProfilePage(page).wait_until_loaded().verify_active_membership(
        journey["dependent_name"], journey["dependent"]["email"], PRIME
    )
    print(f"\n  My Profile of {journey['dependent_name']}: plan {PRIME}, status Active")
    print(f"  {', '.join(MyProfilePage.SERVICES)}: all Active")
