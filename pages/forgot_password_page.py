import re

from playwright.sync_api import Page, expect


class ForgotPasswordPage:
    """/forgot-password: enter the email, then the 6-digit code sent to it."""

    URL_PATTERN = re.compile(r"/forgot-password")
    CODE_LENGTH = 6

    def __init__(self, page: Page):
        self.page = page
        # Written "Password Reset - Two-Factor Authentication"; CSS shows it in capitals.
        self.heading = page.get_by_text("Password Reset - Two-Factor Authentication", exact=True)
        self.email_input = page.get_by_placeholder("Type your email address")
        self.send_code_button = page.get_by_role("button", name=re.compile(r"^send code$", re.I))

        # Shown after Send Code: one single-digit box per code digit, then Verify.
        self.code_sent_message = page.get_by_text("We've sent a 6-digit verification code to your email address.")
        self.code_inputs = page.locator("input[inputmode='numeric'][maxlength='1']")
        self.verify_button = page.get_by_role("button", name=re.compile(r"^verify$", re.I))

    def wait_until_loaded(self, timeout: float = 60_000):
        expect(self.page).to_have_url(self.URL_PATTERN, timeout=timeout)
        expect(self.email_input).to_be_visible(timeout=timeout)
        return self

    def send_code(self, email: str):
        self.email_input.fill(email)
        self.send_code_button.click()
        expect(self.code_sent_message).to_be_visible(timeout=60_000)
        expect(self.code_inputs).to_have_count(self.CODE_LENGTH)

    def enter_code(self, code: str):
        # Typing into the first box moves focus to the next one after each digit.
        self.code_inputs.first.click()
        self.page.keyboard.type(code, delay=80)
        for box, digit in zip(self.code_inputs.all(), code):
            expect(box).to_have_value(digit)
