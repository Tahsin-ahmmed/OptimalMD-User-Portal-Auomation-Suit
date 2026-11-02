"""Registration with a referral code (coupon):
page load -> apply referral code -> discount in Enrollment Summary -> register ->
credentials email.

The discount is read from the page (the admin can change the coupon), and the
total must equal plan price minus that discount.
The new Prime member and the emailed password are saved to
test_state/latest_member.json: the login, profile, dashboard and dependents
tests that run next use this member.
Each step is a separate test; when one fails, the rest are skipped.
"""
import re

import pytest
from playwright.sync_api import expect

from pages.registration_page import RegistrationPage
from pages.welcome_page import WelcomePage
from utils.email_reader import get_login_credentials
from utils.member_store import save_latest_member, update_latest_member
from utils.test_data import PRIME, REFERRAL_CODE, VALID_CARD, new_member

pytestmark = pytest.mark.smoke

PLAN = PRIME  # the default plan on the registration page


def test_step1_registration_page_loads_without_discount(journey):
    registration = RegistrationPage(journey["new_page"]()).open()
    journey["registration"] = registration

    expect(registration.selected_plan_name, "Default plan").to_have_text(PLAN)
    expect(registration.referral_code_input, "Referral code field").to_be_visible()
    expect(registration.referral_discount_label, "No discount before a code is applied").to_have_count(0)

    journey["plan_price"] = registration.dollars(registration.plan_price.inner_text())
    total = registration.dollars(registration.total_monthly_cost.inner_text())
    assert total == journey["plan_price"], f"Total ${total} should equal the plan price ${journey['plan_price']} before a code"
    print(f"\n  {PLAN}: plan ${journey['plan_price']:.2f}, total ${total:.2f}/month, no discount")


def test_step2_apply_referral_code(journey):
    registration = journey["registration"]
    response = registration.apply_referral_code(REFERRAL_CODE)
    assert response.ok, f"Referral code {REFERRAL_CODE} was rejected: {response.status} {response.text()}"

    # "Awesome! Discount Applied" popup covers the form until "Got it!" is clicked.
    expect(registration.discount_popup_title, "'Discount Applied' popup").to_be_visible()
    expect(registration.discount_popup_referred_by, "'Referred by' in popup").to_be_visible()
    discount = registration.dollars(registration.referral_discount_amount.inner_text())
    assert discount > 0, "Referral code applied but the discount is $0"
    popup_discount = registration.dollars(registration.discount_popup_amount.inner_text())
    assert popup_discount == discount, f"Popup says ${popup_discount:g} OFF but the summary discount is ${discount:.2f}"
    registration.close_discount_popup()
    print(f"\n  'Awesome! Discount Applied' popup: ${popup_discount:g} OFF, closed with 'Got it!'")

    expect(registration.referral_message, "Discount message").to_be_visible()
    expect(registration.referral_discount_label, "Referral code row").to_contain_text(REFERRAL_CODE)
    expected_total = journey["plan_price"] - discount
    total = registration.dollars(registration.total_monthly_cost.inner_text())
    assert total == expected_total, (
        f"Total ${total:.2f}/month should be plan ${journey['plan_price']:.2f} minus discount ${discount:.2f} = ${expected_total:.2f}"
    )
    journey["total"] = total
    print(
        f"  Referral code {REFERRAL_CODE} applied: '{registration.referral_message.inner_text()}'"
        f"\n  Plan ${journey['plan_price']:.2f} - discount ${discount:.2f} = total ${total:.2f}/month"
    )


def test_step3_register_with_referral_code(journey):
    registration = journey["registration"]
    member = new_member()
    journey["member"] = member
    journey["full_name"] = f"{member['first_name']} {member['last_name']}"
    print(
        f"\n  Member: {member['first_name']} {member['last_name']} | {member['email']} | {member['phone']} | DOB {member['dob']}"
        f"\n  Plan  : {PLAN} with referral code {REFERRAL_CODE} | card ending {VALID_CARD['number'][-4:]}"
    )

    registration.fill_member_info(member)
    registration.fill_card(VALID_CARD)
    registration.accept_terms()
    # The discounted total must still be shown right before paying.
    total_now = registration.dollars(registration.total_monthly_cost.inner_text())
    assert total_now == journey["total"], f"Total changed to ${total_now:.2f} before paying (expected ${journey['total']:.2f})"
    registration.submit()

    WelcomePage(registration.page).wait_until_loaded().verify_account_created()
    save_latest_member(member, PLAN)
    print(f"  Account created at ${journey['total']:.2f}/month, welcome page shown (member saved)")


def test_step4_receive_credentials_email(journey):
    email = journey["member"]["email"]
    credentials = get_login_credentials(email)
    journey["credentials"] = credentials
    update_latest_member(password=credentials["password"])
    print(f"\n  Credentials email received: username={credentials['username']} password={credentials['password']} (saved)")

    assert credentials["username"] == email, (
        f"Username in email ({credentials['username']}) does not match registered email ({email})"
    )
    assert re.fullmatch(r"\S{6,}", credentials["password"]), "Temporary password in email looks invalid"

