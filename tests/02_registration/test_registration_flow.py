"""Registration page checked in one browser tab, without reloading between steps:
page load -> empty submit errors -> plan prices -> register a new Prime (Individual) member.

Run with:  pytest tests/02_registration
Each step is a separate test so the report shows where it breaks. When a step
fails, the rest are skipped.
"""
import pytest
from playwright.sync_api import expect

from pages.registration_page import RegistrationPage
from pages.welcome_page import WelcomePage
from utils.test_data import PRIME, PRIME_INDIVIDUAL, VALID_CARD, new_member

pytestmark = pytest.mark.smoke

PLAN = PRIME_INDIVIDUAL  # the plan registered in step 4
PLAN_PRICES = [(PRIME, "$149"), (PRIME_INDIVIDUAL, "$99")]

EMPTY_FORM_ERRORS = [
    "A valid first name with only characters A-Z or a-z is required.",
    "A valid last name with only characters A-Z or a-z is required.",
    "A valid email is required.",
    "A valid phone number with 10 digits is required.",
    "Date of birth is required.",
    "Card number must be 13 to 19 digits.",
    "Expiry date must be in MM/YY format.",
    "CVC must be 3 or 4 digits.",
    "You must accept the terms and conditions.",
]


def test_step1_registration_page_loads(journey):
    registration = RegistrationPage(journey["new_page"]()).open()
    journey["registration"] = registration

    expect(registration.first_name_input, "First name field").to_be_visible()
    expect(registration.submit_button, "Submit button").to_be_enabled()
    expect(registration.selected_plan_name, "Default plan").to_have_text(PRIME)
    expect(registration.total_monthly_cost, "Default price").to_contain_text("$149")
    print(f"\n  Registration page loaded, default plan {PRIME} at $149")


def test_step2_empty_submit_shows_all_errors(journey):
    registration = journey["registration"]
    registration.submit()

    for message in EMPTY_FORM_ERRORS:
        expect(registration.error_message(message), f"Error: {message}").to_be_visible()
    print(f"\n  Empty submit: all {len(EMPTY_FORM_ERRORS)} validation errors shown")


def test_step3_plan_selection_updates_price(journey):
    registration = journey["registration"]
    print()
    # Ends on Prime (Individual), the plan registered in the next step.
    for plan, price in PLAN_PRICES:
        registration.select_plan(plan)
        expect(registration.selected_plan_name, "Selected plan in Enrollment Summary").to_have_text(plan)
        expect(registration.total_monthly_cost, f"Monthly cost for {plan}").to_contain_text(price)
        print(f"  {plan}: {price}/month")


def test_step4_register_new_member(journey):
    registration = journey["registration"]
    member = new_member()
    print(
        f"\n  Member: {member['first_name']} {member['last_name']} | {member['email']} | {member['phone']} | DOB {member['dob']}"
        f"\n  Plan  : {PLAN} | card ending {VALID_CARD['number'][-4:]}"
    )

    expect(registration.selected_plan_name, "Plan being purchased").to_have_text(PLAN)
    registration.fill_member_info(member)
    registration.fill_card(VALID_CARD)
    registration.accept_terms()
    registration.submit()

    WelcomePage(registration.page).wait_until_loaded().verify_account_created()
    print("  Account created, welcome page shown")
