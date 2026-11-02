"""The saved member completes the profile wizard (demographics, address, payment) and activates.

Runs in the shared logged-in tab, right after the login test. Activation only
works once, so a member that is already activated is skipped: run the
registration tests first for a new member.
"""
import pytest
from playwright.sync_api import expect

from pages.dashboard_page import DashboardPage
from pages.update_profile_page import UpdateProfilePage
from utils.member_store import update_latest_member
from utils.test_data import VALID_CARD, new_profile_details


@pytest.mark.smoke
def test_saved_member_activates_profile(logged_in_member):
    member = logged_in_member["member"]
    if member["address"]:
        pytest.skip(f"{logged_in_member['full_name']} is already activated. Run the registration tests for a new member.")
    page = logged_in_member["page"]
    details = new_profile_details()
    address = details["address"]

    dashboard = DashboardPage(page)
    if not dashboard.is_showing():
        dashboard.open()
    dashboard.start_profile_completion()

    profile = UpdateProfilePage(page).wait_until_loaded()
    profile.verify_personal_details(member)
    print(f"\n  Step 1: personal details pre-filled, gender = {details['gender']}")
    profile.complete_personal_demographics(details["gender"])

    print(f"  Step 2: address = {address['street']}, {address['city']}, {address['state']} {address['zip']}")
    profile.complete_contact_information(address)

    # Every registration test pays with the same test card.
    profile.verify_payment_on_file(VALID_CARD)
    print(f"  Step 3: card ending {VALID_CARD['number'][-4:]} on file")
    profile.continue_from_payment()

    profile.activate()
    print("  Step 4: activated, 'Updated!' popup shown")
    profile.close_updated_popup()
    member["address"] = address
    update_latest_member(address=address)

    dashboard.wait_until_loaded()
    expect(dashboard.profile_completion(100), "Profile completion 100%").to_be_visible()
    expect(dashboard.current_plan(member["plan"]), f"Current plan '{member['plan']}'").to_be_visible()
    print(f"  Profile 100% complete, current plan: {member['plan']} (address saved)")
