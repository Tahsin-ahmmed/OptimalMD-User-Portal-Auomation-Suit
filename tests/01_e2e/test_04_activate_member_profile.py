"""E2E step 4: the member completes the profile wizard (demographics, address, payment) and activates."""
import pytest

from pages.dashboard_page import DashboardPage
from pages.update_profile_page import UpdateProfilePage
from utils.member_store import update_latest_member
from utils.test_data import VALID_CARD, new_profile_details

pytestmark = pytest.mark.e2e
JOURNEY = "new_member"


def test_step4_complete_profile_and_activate(journey):
    page = journey["page"]
    details = new_profile_details()
    address = details["address"]

    DashboardPage(page).start_profile_completion()
    profile = UpdateProfilePage(page).wait_until_loaded()

    profile.verify_personal_details(journey["member"])
    print(f"\n  Personal details pre-filled correctly; gender = {details['gender']}")
    profile.complete_personal_demographics(details["gender"])

    print(f"  Address = {address['street']}, {address['city']}, {address['state']} {address['zip']}")
    profile.complete_contact_information(address)

    profile.verify_payment_on_file(VALID_CARD)
    print(f"  Card ending {VALID_CARD['number'][-4:]} on file")
    profile.continue_from_payment()

    profile.activate()
    print("  Activated, 'Updated!' popup shown")
    profile.close_updated_popup()
    journey["address"] = address
    update_latest_member(address=address)
