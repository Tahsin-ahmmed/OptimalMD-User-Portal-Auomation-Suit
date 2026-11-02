"""Prime members can add up to 7 dependents from Manage Profile.

Uses the saved Prime member in the shared logged-in tab (see conftest.py),
then runs in file order: add an adult dependent, add a child dependent, and
log in as the adult (in a separate browser) with the credentials emailed to them.
"""
import re

import pytest
from playwright.sync_api import expect

from pages.dashboard_page import DashboardPage
from pages.login_page import LoginPage
from utils.email_reader import DEPENDENT_SUBJECT, get_login_credentials
from utils.test_data import PRIME, new_dependent


def _add_and_activate(prime_member, profile, dependent):
    relation = dependent["relation"]
    full_name = f"{dependent['first_name']} {dependent['last_name']}"

    profile.add_dependent(relation)
    print(f"\n  {relation} added: 'Dependent Added Successfully!' popup closed with Done")

    profile.fill_dependent_demographics(dependent)
    profile.next_button.click()
    expect(profile.step_heading("Contact Information")).to_be_visible()
    contact = f", {dependent['email']}, {dependent['phone']}" if dependent["adult"] else ""
    print(f"  Step 1: {full_name}, {dependent['gender']}, born {dependent['dob']}{contact}")

    profile.copy_primary_address(prime_member["address"])
    print("  Step 2: 'Copy Primary Address' filled the member's address")

    profile.activate_dependent(full_name)
    print(f"  Step 3: activated, 'Updated!' popup shown for {full_name}")

    # The details are only saved on Activate, so check they survive a reload.
    profile.open()
    expect(profile.dependent_card(full_name)).to_contain_text(f"({relation})")
    print(f"  Sidebar shows {full_name} ({relation}) after reload")


def test_add_adult_dependent(prime_member, member_profile):
    dependent = new_dependent(prime_member["adult_relation"])
    _add_and_activate(prime_member, member_profile, dependent)
    prime_member["dependents"]["adult"] = dependent


def test_add_child_dependent(prime_member, member_profile):
    dependent = new_dependent("Child")
    _add_and_activate(prime_member, member_profile, dependent)
    prime_member["dependents"]["child"] = dependent


def test_adult_dependent_logs_in_with_emailed_credentials(prime_member):
    dependent = prime_member["dependents"].get("adult")
    if not dependent:
        pytest.skip("The adult dependent was not activated, so there is no login to check")
    full_name = f"{dependent['first_name']} {dependent['last_name']}"

    credentials = get_login_credentials(dependent["email"], DEPENDENT_SUBJECT)
    print(f"\n  'Registered as Dependent' email received: {credentials['username']} / {credentials['password']}")
    assert credentials["username"] == dependent["email"], (
        f"Email in the credentials email ({credentials['username']}) does not match the dependent's ({dependent['email']})"
    )
    assert re.fullmatch(r"\S{6,}", credentials["password"]), "Temporary password in email looks invalid"

    page = prime_member["new_page"]()
    LoginPage(page).open().login(credentials["username"], credentials["password"])
    dashboard = DashboardPage(page).wait_until_loaded()

    # The member already activated this dependent, so their profile is complete on first login.
    expect(dashboard.member_name(full_name), "Dependent's name on dashboard").to_be_visible()
    expect(dashboard.profile_completion(100), "Profile completion 100%").to_be_visible()
    expect(dashboard.current_plan(PRIME), f"Current plan '{PRIME}'").to_be_visible()
    expect(dashboard.complete_profile_popup, "No 'complete your profile' popup").to_be_hidden()
    print(f"  Logged in as {full_name}: 100% complete, plan {PRIME}")
