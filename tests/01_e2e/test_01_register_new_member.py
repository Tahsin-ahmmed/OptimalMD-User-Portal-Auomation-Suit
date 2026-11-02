"""E2E step 1: a new member registers on the Prime plan and sees the welcome page.

The e2e steps are one file each (test_01 ... test_11) and share one browser
journey, so run the whole folder:  pytest tests/01_e2e
When a step fails, the later steps are skipped.
"""
import pytest
from playwright.sync_api import expect

from pages.registration_page import RegistrationPage
from pages.welcome_page import WelcomePage
from utils.member_store import save_latest_member
from utils.test_data import PRIME, VALID_CARD, new_member

pytestmark = pytest.mark.e2e
JOURNEY = "new_member"


def test_step1_register_new_member(journey):
    member = new_member()
    journey["member"] = member
    journey["full_name"] = f"{member['first_name']} {member['last_name']}"
    print(
        f"\n  Member: {journey['full_name']} | {member['email']} | {member['phone']} | DOB {member['dob']}"
        f"\n  Plan  : {PRIME}"
    )

    registration = RegistrationPage(journey["new_page"]()).open()
    registration.select_plan(PRIME)
    expect(registration.selected_plan_name, "Selected plan in Enrollment Summary").to_have_text(PRIME)

    registration.fill_member_info(member)
    registration.fill_card(VALID_CARD)
    registration.accept_terms()
    registration.submit()

    WelcomePage(journey["page"]).wait_until_loaded().verify_account_created()
    save_latest_member(member, PRIME)
    print("  Account created, welcome page shown (saved as the member for the dependents tests)")
