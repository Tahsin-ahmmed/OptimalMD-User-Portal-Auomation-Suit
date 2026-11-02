import re

from playwright.sync_api import Page, expect


class ChangePasswordPage:
    """/change-password, opened from the profile menu's "Change Password".

    Update checks the current password and emails a 6-digit code; after the code
    is verified the password changes, "Successfully done!" is shown and Done logs
    the member out to /login.
    """

    URL_PATTERN = re.compile(r"/change-password")
    CODE_LENGTH = 6
    REQUIREMENTS = ["At least 6 characters", "1 uppercase letter", "1 lowercase letter", "1 number", "1 special character"]

    def __init__(self, page: Page):
        self.page = page
        # Shown in capitals by CSS; the text itself is "Change your password".
        self.heading = page.get_by_text("Change your password", exact=True)
        self.current_password_input = page.get_by_placeholder("Please enter your current password")
        self.new_password_input = page.get_by_placeholder("Create a new password")
        self.confirm_password_input = page.get_by_placeholder("Re-enter your new password to confirm")
        # Another "Update" button exists on the page, so this one is scoped to the form card.
        self.form = self.heading.locator("xpath=..")
        self.update_button = self.form.get_by_role("button", name=re.compile(r"^update$", re.I))

        # "Verify Code" popup: one single-digit box per code digit, then Verify.
        self.verify_code_heading = page.get_by_role("heading", name="Verify Code", exact=True)
        self.code_sent_message = page.get_by_text("We've sent a 6-digit verification code to your email address.")
        self.code_inputs = page.locator("input[inputmode='numeric'][maxlength='1']")
        self.verify_button = page.get_by_role("button", name=re.compile(r"^verify$", re.I))

        self.success_popup = page.get_by_role("dialog").filter(has_text="Password changed successfully")
        self.success_done_button = self.success_popup.get_by_role("button", name=re.compile(r"^done$", re.I))

    def wait_until_loaded(self, timeout: float = 60_000):
        expect(self.page).to_have_url(self.URL_PATTERN, timeout=timeout)
        expect(self.current_password_input).to_be_visible(timeout=timeout)
        return self

    def requirement(self, text: str):
        return self.page.get_by_text(text, exact=True)

    def error_message(self, text: str):
        return self.page.get_by_text(text, exact=True)

    def submit(self, current_password: str, new_password: str):
        """Fill the form and click Update; the "Verify Code" popup opens once the code is emailed."""
        self.current_password_input.fill(current_password)
        self.new_password_input.fill(new_password)
        self.confirm_password_input.fill(new_password)
        self.update_button.click()
        expect(self.verify_code_heading).to_be_visible(timeout=60_000)
        expect(self.code_inputs).to_have_count(self.CODE_LENGTH)

    def enter_code(self, code: str):
        # Typing into the first box moves focus to the next one after each digit.
        self.code_inputs.first.click()
        self.page.keyboard.type(code, delay=80)
        for box, digit in zip(self.code_inputs.all(), code):
            expect(box).to_have_value(digit)

    def close_success_popup(self):
        self.success_done_button.click()
        expect(self.success_popup).to_be_hidden()
