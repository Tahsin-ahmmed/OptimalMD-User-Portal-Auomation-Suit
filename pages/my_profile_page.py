import re

from playwright.sync_api import Page, expect


class MyProfilePage:
    """My Profile (/my-profile/<id>), opened from the name/avatar menu."""

    URL_PATTERN = re.compile(r"/my-profile/")
    SERVICES = ["Pharmacy access", "Clinic access", "OptimalMD AI"]

    def __init__(self, page: Page):
        self.page = page
        self.membership = page.locator("section").filter(has=page.get_by_role("heading", name="Membership", exact=True))
        # Each value sits right after its label: <p>Status</p><p><span>Active</span></p>
        self.current_plan = self.membership.locator("xpath=.//p[normalize-space()='Current plan']/following-sibling::p[1]")
        self.status = self.membership.locator("xpath=.//p[normalize-space()='Status']/following-sibling::p[1]")

    def wait_until_loaded(self, timeout: float = 120_000):
        expect(self.page).to_have_url(self.URL_PATTERN, timeout=timeout)
        expect(self.current_plan).to_be_visible(timeout=timeout)
        return self

    def name_heading(self, full_name: str):
        return self.page.get_by_role("heading", level=1, name=full_name)

    def email(self, address: str):
        return self.page.get_by_text(address, exact=True).first

    def verify_active_membership(self, full_name: str, email: str, plan: str):
        """Name and email shown, plan and status Active, and every service Active."""
        expect(self.name_heading(full_name), "Name on My Profile").to_be_visible()
        expect(self.email(email), "Email on My Profile").to_be_visible()
        expect(self.current_plan, "Current plan").to_have_text(re.compile(f"^{re.escape(plan)}$", re.I))
        expect(self.status, "Membership status").to_have_text("Active")
        for service in self.SERVICES:
            expect(self.service_status(service), f"'{service}' status").to_have_text("Active")

    def service_status(self, service: str):
        # Each service row is <span>Pharmacy access</span><span>Active</span>
        return self.membership.locator(f"xpath=.//span[normalize-space()='{service}']/following-sibling::span[1]")
