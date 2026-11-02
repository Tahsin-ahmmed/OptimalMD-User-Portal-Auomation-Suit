"""E2E step 8: the member logs out from the profile menu and lands on the login page."""
import re

import pytest
from playwright.sync_api import expect

from pages.dashboard_page import DashboardPage
from pages.login_page import LoginPage

pytestmark = pytest.mark.e2e
JOURNEY = "new_member"


def test_step8_member_logs_out(journey):
    page = journey["page"]
    DashboardPage(page).open().logout()

    login = LoginPage(page)
    expect(page, "Logout goes to the login page").to_have_url(re.compile(r"/login"), timeout=60_000)
    expect(login.email_input, "Login form shown after logout").to_be_visible(timeout=60_000)
    print(f"\n  {journey['full_name']} logged out, login page shown")
