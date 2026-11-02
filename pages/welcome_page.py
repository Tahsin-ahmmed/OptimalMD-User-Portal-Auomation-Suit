import re

from playwright.sync_api import Page, expect


class WelcomePage:
    URL_PATTERN = re.compile(r"/welcome")

    def __init__(self, page: Page):
        self.page = page
        self.success_heading = page.get_by_role("heading", name="Account Created Successfully!")
        self.confirmation_text = page.get_by_text(
            "Your account has been successfully created. "
            "A confirmation email has been sent to your registered email address."
        )
        self.check_email_title = page.get_by_text("Check your email", exact=True)
        self.check_email_text = page.get_by_text("We've sent login instructions and next steps to your inbox")
        self.all_set_heading = page.get_by_role("heading", name="You're All Set!")
        self.login_button = page.get_by_text("Login to Your Account")
        self.need_help_button = page.get_by_text("Need Help?", exact=True)

    def wait_until_loaded(self, timeout: float = 60_000):
        expect(self.page).to_have_url(self.URL_PATTERN, timeout=timeout)
        expect(self.success_heading).to_be_visible(timeout=timeout)
        return self

    def verify_account_created(self):
        expect(self.success_heading).to_be_visible()
        expect(self.confirmation_text).to_be_visible()
        expect(self.check_email_title).to_be_visible()
        expect(self.check_email_text).to_be_visible()
        expect(self.all_set_heading).to_be_visible()
        expect(self.login_button).to_be_visible()
        expect(self.need_help_button).to_be_visible()
