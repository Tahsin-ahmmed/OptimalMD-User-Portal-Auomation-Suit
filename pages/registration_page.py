import re

from playwright.sync_api import Page, expect


class RegistrationPage:
    URL_PATH = "/register"

    def __init__(self, page: Page):
        self.page = page

        # The hidden "Secure Payment" popup reuses the same input names,
        # so every form field is scoped to the #form container.
        self.form = page.locator("#form")

        self.first_name_input = self.form.locator("input[name='fName']")
        self.last_name_input = self.form.locator("input[name='lName']")
        self.email_input = self.form.locator("input[name='email']")
        self.phone_input = self.form.locator("input[name='phoneNumber']")
        self.dob_input = self.form.get_by_placeholder("MM/DD/YYYY")

        self.referral_code_input = self.form.locator("input[name='coupon']")
        self.apply_referral_button = self.form.get_by_role("button", name="Apply")

        self.card_number_input = self.form.locator("input[name='cardNumber']")
        self.expiration_input = self.form.locator("input[name='expiration']")
        self.cvc_input = self.form.locator("input[name='cvc']")

        self.terms_checkbox = (
            self.form.get_by_text("I agree to the")
            .locator("xpath=ancestor::label[1]")
            .locator("input[type='checkbox']")
        )
        self.submit_button = page.get_by_role("button", name="Complete Payment & Send Login Instructions")

        # Clicking a plan card opens its details popup; "Select Plan" confirms the choice.
        self.select_plan_button = page.get_by_role("button", name="Select Plan")
        self.selected_plan_name = page.get_by_text("Charged Immediately").locator("xpath=preceding-sibling::*[1]")
        self.total_monthly_cost = (
            page.get_by_text(re.compile("^Total Monthly Cost$", re.I))
            .locator("xpath=ancestor::div[.//p[contains(., '/month')]][1]")
            .locator("p", has_text="/month")
        )

        # Enrollment Summary rows: <span>Plan</span><span>$149.00</span> and, once a
        # referral code is applied, <span>Referral Code "OMD-..."</span><span>− $9.00</span>
        self.enrollment_summary = page.get_by_text("Enrollment Summary", exact=True).locator("xpath=..")
        self.plan_price = self.enrollment_summary.locator("xpath=.//span[normalize-space()='Plan']/following-sibling::span[1]")
        self.referral_discount_label = self.enrollment_summary.locator("xpath=.//span[starts-with(normalize-space(), 'Referral Code')]")
        self.referral_discount_amount = self.referral_discount_label.locator("xpath=following-sibling::span[1]")
        self.referral_message = self.enrollment_summary.get_by_text(re.compile(r"off every month"))

        # "Awesome! Discount Applied / $9 OFF / Referred by ..." popup shown after Apply.
        self.discount_popup_title = page.get_by_text("Discount Applied", exact=True)
        self.discount_popup_amount = page.get_by_text(re.compile(r"^\$[\d.]+ OFF$"))
        self.discount_popup_referred_by = page.get_by_text("Referred by", exact=True)
        self.discount_popup_got_it_button = page.get_by_role("button", name="Got it!")

    def open(self, timeout: float = 120_000):
        # Staging serves a 14 MB uncompressed JS bundle that can take ~60s to
        # download, so wait for the first field instead of a page load event.
        self.page.goto(self.URL_PATH, wait_until="commit")
        self.first_name_input.wait_for(state="visible", timeout=timeout)
        return self

    def plan_card(self, plan_name: str):
        return self.page.get_by_role("heading", name=plan_name, exact=True).locator(
            "xpath=ancestor::div[contains(@style, '--plan-accent-color')]"
        )

    def select_plan(self, plan_name: str):
        self.plan_card(plan_name).get_by_role("button", name="See Details").click()
        self.select_plan_button.click()
        expect(self.select_plan_button).to_be_hidden()

    def fill_member_info(self, member: dict):
        self.first_name_input.fill(member["first_name"])
        self.last_name_input.fill(member["last_name"])
        self.email_input.fill(member["email"])
        self.phone_input.fill(member["phone"])
        # The date field is masked, so type it key by key and close the calendar.
        self.dob_input.click()
        self.dob_input.press_sequentially(member["dob"], delay=50)
        self.page.keyboard.press("Escape")

    def fill_card(self, card: dict):
        self.card_number_input.fill(card["number"])
        self.expiration_input.press_sequentially(card["expiry"].replace("/", ""), delay=50)
        self.cvc_input.fill(card["cvc"])

    def apply_referral_code(self, code: str):
        """Apply the code and return the server's reply to the coupon check."""
        self.referral_code_input.fill(code)
        with self.page.expect_response(lambda r: "/api/coupons/single-coupon" in r.url, timeout=60_000) as response:
            self.apply_referral_button.click()
        return response.value

    def close_discount_popup(self):
        self.discount_popup_got_it_button.click()
        expect(self.discount_popup_title).to_be_hidden()

    @staticmethod
    def dollars(text: str) -> float:
        """"$149.00", "− $9.00" or "$140/month" -> 149.0, 9.0, 140.0"""
        return float(re.search(r"\$([\d,]+(?:\.\d+)?)", text).group(1).replace(",", ""))

    def accept_terms(self):
        self.terms_checkbox.check(force=True)

    def submit(self):
        self.submit_button.click()

    def register(self, plan_name: str, member: dict, card: dict):
        self.select_plan(plan_name)
        self.fill_member_info(member)
        self.fill_card(card)
        self.accept_terms()
        self.submit()

    def error_message(self, text: str):
        return self.form.get_by_text(text)
