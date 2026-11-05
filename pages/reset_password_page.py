import re

from playwright.sync_api import Page, expect


class ResetPasswordPage:
    """/app/omd/reset-password?token=...: opened from the "Create New Password" email button."""

    URL_PATTERN = re.compile(r"/reset-password\?token=")
    REQUIREMENTS = ["At least 6 characters", "1 uppercase letter", "1 lowercase letter", "1 number", "1 special character"]

    def __init__(self, page: Page):
        self.page = page
        # CSS shows the heading in capitals, so match it regardless of case.
        self.heading = page.get_by_text(re.compile(r"^reset your password$", re.I))
        self.new_password_input = page.get_by_placeholder("Enter your new password")
        self.confirm_password_input = page.get_by_placeholder("Confirm your new password")
        self.reset_button = page.get_by_role("button", name=re.compile(r"^reset$", re.I))

        self.success_message = page.get_by_text("Your password has been reset successfully")
        self.redirect_message = page.get_by_text("Redirecting to login in")

    def open(self, reset_link: str, timeout: float = 120_000):
        self.page.goto(reset_link, wait_until="commit")
        expect(self.page).to_have_url(self.URL_PATTERN, timeout=timeout)
        expect(self.new_password_input).to_be_visible(timeout=timeout)
        return self

    def requirement(self, text: str):
        return self.page.get_by_text(text, exact=True)

    def reset(self, new_password: str):
        self.new_password_input.fill(new_password)
        self.confirm_password_input.fill(new_password)
        self.reset_button.click()
        expect(self.success_message).to_be_visible(timeout=60_000)
