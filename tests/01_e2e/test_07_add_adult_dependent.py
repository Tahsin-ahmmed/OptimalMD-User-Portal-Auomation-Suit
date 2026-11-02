"""E2E step 7: the member adds an adult dependent (Spouse) in Manage Profile and activates them."""
import pytest
from playwright.sync_api import expect

from pages.update_profile_page import UpdateProfilePage
from utils.test_data import new_dependent

pytestmark = pytest.mark.e2e
JOURNEY = "new_member"


def test_step7_add_adult_dependent(journey):
    dependent = new_dependent("Spouse")
    journey["dependent"] = dependent
    journey["dependent_name"] = f"{dependent['first_name']} {dependent['last_name']}"
    print(f"\n  Dependent: {journey['dependent_name']} (Spouse) | {dependent['email']} | DOB {dependent['dob']}")

    profile = UpdateProfilePage(journey["page"]).open()
    profile.add_dependent("Spouse")
    print("  'Dependent Added Successfully!' popup closed with Done")

    profile.fill_dependent_demographics(dependent)
    profile.next_button.click()
    expect(profile.step_heading("Contact Information"), "Dependent wizard step 2").to_be_visible()
    profile.copy_primary_address(journey["address"])
    print("  'Copy Primary Address' filled the member's address")

    profile.activate_dependent(journey["dependent_name"])
    profile.open()
    expect(profile.dependent_card(journey["dependent_name"]), "Dependent in sidebar after reload").to_contain_text("(Spouse)")
    print(f"  Activated, sidebar shows {journey['dependent_name']} (Spouse)")
