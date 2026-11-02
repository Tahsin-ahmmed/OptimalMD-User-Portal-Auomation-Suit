import re

from playwright.sync_api import Page, expect


class UpdateProfilePage:
    """The 4-step "Manage Profile" wizard a new member completes to activate benefits."""

    URL_PATTERN = re.compile(r"/update-profile")

    def __init__(self, page: Page):
        self.page = page
        self.step_heading = lambda name: page.get_by_role("heading", name=name)
        self.next_button = page.get_by_role("button", name=re.compile(r"^next$", re.I))

        # Step 1: Personal Demographics
        self.first_name_input = page.get_by_placeholder("Type your first name")
        self.last_name_input = page.get_by_placeholder("Type your last name")
        self.email_input = page.get_by_placeholder("Type your email address")
        self.phone_input = page.get_by_placeholder("Type your primary phone number")
        self.dob_input = page.locator("main").get_by_placeholder("MM/DD/YYYY")
        # Gender and State are custom dropdowns: a focusable div that opens a list of option divs.
        self.gender_dropdown = page.locator("div[tabindex='0']").filter(has_text="Gender")

        # Step 2: Contact Information
        self.street_input = page.get_by_placeholder("Your Home Address")
        self.city_input = page.get_by_placeholder("Enter your city name")
        self.state_dropdown = page.locator("div[tabindex='0']").filter(has_text="State").first
        self.zip_input = page.get_by_placeholder("Enter 5-digit ZIP (e.g., 77100)")

        # Step 3: Payment Information
        self.card_number_input = page.locator("main input[name='cardNumber']")
        self.expiration_input = page.locator("main input[name='expiration']")

        # Step 4: Submit Confirmation
        self.activate_button = page.get_by_role("button", name=re.compile(r"^activate$", re.I))

        # SweetAlert2 dialog shown on the dashboard after activation
        self.updated_popup = page.get_by_role("dialog").filter(has_text="You have successfully updated your profile.")
        self.done_button = self.updated_popup.get_by_role("button", name=re.compile(r"^done$", re.I))

        # Dependents (left sidebar + "Select a relation" popup)
        self.add_dependent_button = page.get_by_role("button", name=re.compile(r"add dependent", re.I))
        self.relation_popup = page.locator("div.fixed.opacity-100").filter(has_text="Select a relation")
        self.dependent_added_popup = page.locator("div.fixed.opacity-100").filter(has_text="Dependent Added Successfully!")
        self.dependent_added_done_button = self.dependent_added_popup.get_by_role("button", name=re.compile(r"^done$", re.I))
        self.dependent_cards = page.locator(
            "xpath=//*[normalize-space()='Your Dependents']/following-sibling::div[contains(@class, 'rounded-md')]"
        )
        # Only shown while a dependent (not the member) is open in the form.
        self.remove_button = page.get_by_role("button", name=re.compile(r"remove", re.I))
        self.copy_address_checkbox = page.locator("label").filter(has_text="Copy Primary Address").locator("input[type='checkbox']")
        self.remove_confirm_popup = page.get_by_role("dialog").filter(has_text="Are you sure?")
        self.confirm_remove_button = self.remove_confirm_popup.get_by_role("button", name="Yes, remove it!")
        self.dependent_updated_popup = page.get_by_role("dialog").filter(has_text="information updated successfully")
        self.dependent_done_button = self.dependent_updated_popup.get_by_role("button", name=re.compile(r"^done$", re.I))

    def wait_until_loaded(self, timeout: float = 60_000):
        expect(self.page).to_have_url(self.URL_PATTERN, timeout=timeout)
        expect(self.step_heading("Personal Demographics")).to_be_visible(timeout=timeout)
        return self

    def _choose(self, dropdown, option: str):
        dropdown.click()
        # The open dropdown lists its options in an "omd-modal-scroll" box.
        options = self.page.locator(".omd-modal-scroll").filter(visible=True)
        options.get_by_text(option, exact=True).click()
        expect(dropdown).to_contain_text(option)

    def verify_personal_details(self, member: dict):
        expect(self.first_name_input).to_have_value(member["first_name"])
        expect(self.last_name_input).to_have_value(member["last_name"])
        expect(self.email_input).to_have_value(member["email"])
        expect(self.dob_input).to_have_value(member["dob"])
        digits = member["phone"]
        expect(self.phone_input).to_have_value(f"({digits[:3]}) {digits[3:6]}-{digits[6:]}")

    def complete_personal_demographics(self, gender: str):
        self._choose(self.gender_dropdown, gender)
        self.next_button.click()
        expect(self.step_heading("Contact Information")).to_be_visible()

    def complete_contact_information(self, address: dict):
        self.street_input.fill(address["street"])
        self.city_input.fill(address["city"])
        self._choose(self.state_dropdown, address["state"])
        self.zip_input.fill(address["zip"])
        self.next_button.click()
        expect(self.step_heading("Payment Information")).to_be_visible()

    def verify_payment_on_file(self, card: dict):
        expect(self.card_number_input).to_have_value(re.compile(card["number"][-4:] + "$"))
        expect(self.expiration_input).to_have_value(card["expiry"])

    def continue_from_payment(self):
        self.next_button.click()
        expect(self.step_heading("Submit Confirmation")).to_be_visible()

    def activate(self):
        self.activate_button.click()
        expect(self.updated_popup).to_be_visible(timeout=60_000)

    def close_updated_popup(self):
        self.done_button.click()
        expect(self.updated_popup).to_be_hidden()

    # --- Dependents ---------------------------------------------------------

    def open(self, timeout: float = 120_000):
        self.page.goto("/update-profile", wait_until="commit")
        return self.wait_until_loaded(timeout)

    def dependent_count(self) -> int:
        # The dependent cards load a moment after the page itself.
        expect(self.add_dependent_button).to_be_visible()
        self.page.wait_for_timeout(3000)
        return self.dependent_cards.count()

    def dependent_card(self, full_name: str):
        return self.dependent_cards.filter(has_text=full_name)

    def remove_unfinished_dependents(self) -> int:
        """Remove dependents that were added but never activated (e.g. by a failed run).

        While one exists, Add Dependent doesn't open the relation popup. Activated
        dependents show "First Last (Relation)"; unfinished ones show only the relation.
        """
        unfinished = self.dependent_cards.filter(has_not_text="(")
        removed = 0
        while unfinished.count():
            count = self.dependent_cards.count()
            # A hidden "Complete" label from the card's progress ring sits on top of the text,
            # so force the click; it still lands on the card's own click handler.
            unfinished.first.locator("p").last.click(force=True)
            expect(self.remove_button).to_be_visible(timeout=60_000)
            self.remove_button.click()
            expect(self.remove_confirm_popup).to_be_visible()
            self.confirm_remove_button.click()
            expect(self.dependent_cards).to_have_count(count - 1, timeout=60_000)
            removed += 1
        return removed

    def add_dependent(self, relation: str):
        self.add_dependent_button.click()
        expect(self.relation_popup).to_be_visible()
        self.relation_popup.get_by_text(relation, exact=True).click()
        # Choosing a relation creates the dependent on the server straight away.
        expect(self.dependent_added_popup).to_be_visible(timeout=120_000)
        expect(self.dependent_added_popup).to_contain_text("Your dependent has been added to your profile.")
        self.dependent_added_done_button.click()
        expect(self.dependent_added_popup).to_be_hidden()
        expect(self.relation_popup).to_be_hidden()
        expect(self.remove_button).to_be_visible(timeout=60_000)
        expect(self.step_heading("Personal Demographics")).to_be_visible()

    def fill_dependent_demographics(self, dependent: dict):
        self.first_name_input.fill(dependent["first_name"])
        self.last_name_input.fill(dependent["last_name"])
        self._choose(self.gender_dropdown, dependent["gender"])
        self.dob_input.click()
        self.dob_input.press_sequentially(dependent["dob"])
        self.dob_input.press("Escape")
        if dependent["adult"]:
            self.email_input.fill(dependent["email"])
            self.phone_input.fill(dependent["phone"])

    def copy_primary_address(self, address: dict):
        self.copy_address_checkbox.check()
        expect(self.copy_address_checkbox).to_be_checked()
        expect(self.street_input.first).to_have_value(address["street"])
        expect(self.city_input).to_have_value(address["city"])
        expect(self.zip_input).to_have_value(address["zip"])
        # The copied fields are locked so they can't drift from the member's address.
        expect(self.street_input.first).to_be_disabled()
        self.next_button.click()
        expect(self.step_heading("Submit Confirmation")).to_be_visible()

    def activate_dependent(self, full_name: str):
        self.activate_button.click()
        expect(self.dependent_updated_popup).to_be_visible(timeout=60_000)
        expect(self.dependent_updated_popup).to_contain_text("Updated!")
        expect(self.dependent_updated_popup).to_contain_text(f"{full_name} information updated successfully")
        self.dependent_done_button.click()
        expect(self.dependent_updated_popup).to_be_hidden()
