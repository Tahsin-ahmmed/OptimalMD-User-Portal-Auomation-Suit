"""Forgot password, from the login page to logging in with the new password:
login -> Forgot Password? -> send code -> code from email -> verify ->
"Create New Password" link from email -> reset -> login with new password.

Uses the latest Prime member saved by the e2e tests (test_state/latest_member.json)
and saves the new password there, so the dependents tests keep working.
Each step is a separate test; when one fails, the rest are skipped.
"""
import re

import pytest
from playwright.sync_api import expect

from pages.dashboard_page import DashboardPage
from pages.forgot_password_page import ForgotPasswordPage
from pages.login_page import LoginPage
from pages.reset_password_page import ResetPasswordPage
from utils.email_reader import RESET_CODE_SUBJECT, RESET_LINK_SUBJECT, existing_emails, get_reset_code, get_reset_link
from utils.member_store import load_latest_member, update_latest_member
from utils.test_data import new_password

# Blocked by a staging bug: after the code is verified, /api/auth/forgetPassword
# returns 404 "Email not found", so the reset email is never sent.
# Delete this line once the dev team has fixed it.
pytestmark = pytest.mark.skip(reason="Blocked by bug: forgetPassword returns 'Email not found' after code verification")


def test_step1_open_forgot_password_from_login(journey):
    member = load_latest_member()
    if not member:
        pytest.skip("No saved member yet. Run the e2e tests first.")
    journey["member"] = member
    journey["full_name"] = f"{member['first_name']} {member['last_name']}"
    print(f"\n  Member: {journey['full_name']} <{member['email']}>")

    page = journey["new_page"]()
    login = LoginPage(page).open()
    login.forgot_password_link.click()

    forgot = ForgotPasswordPage(page).wait_until_loaded()
    expect(forgot.heading, "Password reset page heading").to_be_visible()
    expect(forgot.send_code_button, "Send Code button").to_be_visible()
    journey["forgot"] = forgot
    print("  'Forgot Password?' opened the password reset page")


def test_step2_send_verification_code(journey):
    email = journey["member"]["email"]
    seen = existing_emails(email, RESET_CODE_SUBJECT)

    journey["forgot"].send_code(email)
    print(f"\n  Send Code: '6-digit verification code' message and {ForgotPasswordPage.CODE_LENGTH} code boxes shown")

    journey["code"] = get_reset_code(email, seen)
    print(f"  'Password Reset Verification code' email received: {journey['code']}")


def test_step3_verify_code_and_receive_reset_link(journey):
    email = journey["member"]["email"]
    forgot = journey["forgot"]
    seen = existing_emails(email, RESET_LINK_SUBJECT)

    forgot.enter_code(journey["code"])
    # Verify checks the code, then asks the server to email the reset link.
    with forgot.page.expect_response(lambda r: "/api/auth/forgetPassword" in r.url, timeout=60_000) as response:
        forgot.verify_button.click()
    assert response.value.ok, (
        f"Code was entered, but sending the reset link failed: "
        f"forgetPassword returned {response.value.status}: {response.value.text()}"
    )
    print("\n  Code verified, server is sending the reset link")

    journey["reset_link"] = get_reset_link(email, seen)
    print("  'Complete Your Password Reset' email received with the 'Create New Password' link")


def test_step4_reset_password(journey):
    reset = ResetPasswordPage(journey["page"]).open(journey["reset_link"])
    expect(reset.heading, "Reset page heading").to_be_visible()
    for rule in ResetPasswordPage.REQUIREMENTS:
        expect(reset.requirement(rule), f"Password requirement '{rule}'").to_be_visible()

    password = new_password()
    reset.reset(password)
    # Saved straight away: from here on, only the new password works.
    journey["new_password"] = password
    update_latest_member(password=password)
    print(f"\n  New password {password}: 'Success! Your password has been reset successfully' shown")

    expect(reset.redirect_message, "Countdown to login").to_be_visible()
    expect(reset.page, "Redirected to the login page").to_have_url(re.compile(r"/login"), timeout=60_000)
    print("  Countdown finished, redirected to the login page")


def test_step5_login_with_new_password(journey):
    page = journey["page"]
    login = LoginPage(page)
    expect(login.email_input, "Login form").to_be_visible(timeout=120_000)
    login.login(journey["member"]["email"], journey["new_password"])

    dashboard = DashboardPage(page).wait_until_loaded()
    expect(dashboard.member_name(journey["full_name"]), "Member name on dashboard").to_be_visible()
    print(f"\n  Logged in as {journey['full_name']} with the new password")
