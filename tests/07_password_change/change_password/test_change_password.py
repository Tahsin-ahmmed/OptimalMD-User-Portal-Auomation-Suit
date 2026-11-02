"""Change password from the profile menu, then log in with the new password:
login -> profile menu "Change Password" -> empty Update errors -> current + new
password -> code from email -> verify -> "Successfully done!" -> logged out ->
login with new password.

Uses the saved member in the shared logged-in tab (see conftest.py) and saves the
new password to test_state/latest_member.json, so later runs keep working.
The code email is the same "Password Reset Verification code" email that
Forgot Password sends (both use /api/otp/send-otp).
Each step is a separate test; when one fails, the rest are skipped.
"""
import re

import pytest
from playwright.sync_api import expect

from pages.change_password_page import ChangePasswordPage
from pages.dashboard_page import DashboardPage
from pages.login_page import LoginPage
from utils.email_reader import RESET_CODE_SUBJECT, existing_emails, get_reset_code
from utils.member_store import update_latest_member
from utils.test_data import new_password


def test_step1_open_change_password_from_profile_menu(journey, logged_in_member):
    # Runs in the shared logged-in tab, like the profile, dashboard and dependents tests.
    journey["session"] = logged_in_member
    journey["member"] = logged_in_member["member"]
    journey["full_name"] = logged_in_member["full_name"]
    page = journey["page"] = logged_in_member["page"]
    print(f"\n  Member: {journey['full_name']} <{journey['member']['email']}>")

    DashboardPage(page).reset().click_profile_menu_item("password")

    change = ChangePasswordPage(page).wait_until_loaded()
    expect(change.heading, "'Change your password' heading").to_be_visible()
    for requirement in ChangePasswordPage.REQUIREMENTS:
        expect(change.requirement(requirement), f"Requirement '{requirement}'").to_be_visible()
    journey["change"] = change
    print("  Profile menu -> 'Change Password' opened /change-password with the password requirements")


def test_step2_empty_update_shows_required_errors(journey):
    change = journey["change"]
    change.update_button.click()

    print("\n  Empty Update:")
    for error in ["Current password is required.", "New password is required.", "Confirm password is required."]:
        expect(change.error_message(error), f"Error '{error}'").to_be_visible()
        print(f"  '{error}'")
    expect(change.verify_code_heading, "No code is sent for an empty form").to_be_hidden()


def test_step3_update_sends_verification_code(journey):
    change = journey["change"]
    email = journey["member"]["email"]
    journey["new_password"] = new_password()
    # Snapshot first, so only the code email sent for this change is read.
    journey["seen_codes"] = existing_emails(email, RESET_CODE_SUBJECT)

    change.submit(journey["member"]["password"], journey["new_password"])
    expect(change.code_sent_message, "Code sent message").to_be_visible()
    print(f"\n  Current password + new password {journey['new_password']} -> Update")
    print("  'Verify Code' popup shown: 6-digit code sent to the email")


def test_step4_verify_code_and_change_password(journey):
    change = journey["change"]
    email = journey["member"]["email"]
    code = get_reset_code(email, journey["seen_codes"])
    print(f"\n  Code from the '{RESET_CODE_SUBJECT}' email: {code}")

    change.enter_code(code)
    change.verify_button.click()
    expect(change.success_popup, "'Successfully done!' popup").to_be_visible(timeout=60_000)
    expect(change.success_popup).to_contain_text("Successfully done!")
    update_latest_member(password=journey["new_password"])
    journey["member"]["password"] = journey["new_password"]
    print("  Verified -> 'Successfully done! Password changed successfully' (new password saved)")

    change.close_success_popup()
    page = change.page
    expect(page, "Done logs the member out to the login page").to_have_url(re.compile(r"/login"), timeout=60_000)
    expect(LoginPage(page).email_input, "Login form shown").to_be_visible(timeout=60_000)
    journey["session"]["logged_in"] = False
    print("  Done -> logged out, login page shown")


def test_step5_login_with_new_password(journey):
    page = journey["change"].page
    LoginPage(page).login(journey["member"]["email"], journey["new_password"])

    dashboard = DashboardPage(page).wait_until_loaded()
    expect(dashboard.member_name(journey["full_name"]), "Member name on dashboard").to_be_visible()
    journey["session"]["logged_in"] = True
    print(f"\n  Logged in as {journey['full_name']} with the new password")
