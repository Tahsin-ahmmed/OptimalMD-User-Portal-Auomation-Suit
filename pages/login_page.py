from playwright.sync_api import Page


class LoginPage:
    URL_PATH = "/login"

    def __init__(self, page: Page):
        self.page = page
        self.email_input = page.locator("input[name='email']")
        self.password_input = page.locator("input[name='password']")
        self.login_button = page.get_by_role("button", name="Log in")
        self.forgot_password_link = page.get_by_role("link", name="Forgot Password?")

    def open(self, timeout: float = 120_000):
        # Same slow 14 MB JS bundle as the registration page.
        self.page.goto(self.URL_PATH, wait_until="commit")
        self.email_input.wait_for(state="visible", timeout=timeout)
        return self

    def login(self, email: str, password: str):
        self.email_input.fill(email)
        self.password_input.fill(password)
        self.login_button.click()
