"""Login with the saved member's email and password; the dashboard shows their name.

Uses the member the registration tests just saved (test_state/latest_member.json),
so no new account is registered here. This login is the one the profile,
dashboard and dependents tests then keep using: the tab stays logged in.
"""
import pytest
from playwright.sync_api import expect

from pages.dashboard_page import DashboardPage
from pages.login_page import LoginPage


@pytest.mark.smoke
def test_login_with_saved_member(member_session):
    if member_session["logged_in"]:
        pytest.skip("The shared tab is already logged in")
    member, full_name, page = member_session["member"], member_session["full_name"], member_session["page"]

    LoginPage(page).open().login(member["email"], member["password"])

    dashboard = DashboardPage(page).wait_until_loaded()
    expect(dashboard.member_name(full_name), "Member name on dashboard").to_be_visible()
    member_session["logged_in"] = True
    print(f"\n  Logged in as {full_name}, dashboard shown (this tab stays logged in for the next tests)")
