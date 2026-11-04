import re

from playwright.sync_api import Page, expect


class DashboardPage:
    URL_PATTERN = re.compile(r"portalstg\.optimalmd\.com/?$")

    def __init__(self, page: Page):
        self.page = page
        self.care_services_heading = page.get_by_role("heading", name="Your Care Services").first

        # Shown on a member's first login. Hidden popups on the page also have
        # "Get Started" buttons, so the buttons are scoped to this popup.
        self.complete_profile_popup = page.locator("div.fixed").filter(
            has_text="Great! Now please complete your profile"
        )
        self.not_now_button = self.complete_profile_popup.get_by_role("button", name="Not Now")
        self.get_started_button = page.locator("button[data-tour='welcome-get-started-btn']")

        # Header. The site marks its parts with data-tour hooks (used by its feature
        # tour); a hidden mobile copy of the header has the same hooks, hence visible=True.
        self.tour_button = page.get_by_role("button", name="Open feature tour menu")
        # The toggle comes first; once open, the language options are buttons in the same block.
        self.language_button = page.locator("[data-tour='nav-language']").filter(visible=True).get_by_role("button").first
        # The name next to the avatar is hidden by CSS, so the avatar opens the profile menu.
        self.profile_avatar = (
            page.locator("[data-tour='header-profile']").filter(visible=True).get_by_role("img", name="Profile")
        )

        # The profile menu items carry data-tour hooks; a hidden mobile copy of the menu also exists.
        self.profile_menu_item = lambda name: page.locator(f"li[data-tour='profile-item-{name}']").filter(visible=True)

        # My AI Doctor disclaimer. The real checkbox is visually hidden behind a
        # styled box, so it is ticked by clicking its label text like a user would.
        self.ai_doctor_terms_checkbox = page.get_by_role("checkbox", name="I understand and agree to the terms of use.")
        self.ai_doctor_terms_label = page.locator("label").filter(has_text="I understand and agree to the")
        self.ai_doctor_continue_button = page.get_by_role("button", name="OK, Continue")
        # Opening My AI Doctor goes to /ai in the same tab, or shows this error popup.
        # /ai embeds the AI app (ai.optimalmd.com), which signs the member in by itself
        # and can take ~45 s to load; its header has a "Back to Portal" button.
        self.ai_doctor_frame = page.locator("iframe[src*='ai.optimalmd.com']")
        self.ai_doctor_app = page.frame_locator("iframe[src*='ai.optimalmd.com']").get_by_text("Back to Portal")
        self.ai_doctor_error_popup = page.get_by_role("dialog").filter(has_text="Something Went Wrong")

    def open(self, timeout: float = 120_000):
        self.page.goto("/", wait_until="commit")
        return self.wait_until_loaded(timeout)

    def wait_until_loaded(self, timeout: float = 120_000):
        expect(self.page).to_have_url(self.URL_PATTERN, timeout=timeout)
        expect(self.care_services_heading).to_be_visible(timeout=timeout)
        return self

    def dismiss_first_login_popups(self):
        expect(self.complete_profile_popup).to_be_visible()
        self.not_now_button.click()
        expect(self.complete_profile_popup).to_be_hidden()

    def start_profile_completion(self):
        expect(self.complete_profile_popup).to_be_visible()
        self.get_started_button.click()

    def member_name(self, full_name: str):
        # The navbar copy of the name is always hidden by CSS; the Welcome card shows it.
        return self.page.get_by_text(full_name).filter(visible=True).first

    def profile_completion(self, percent: int):
        return self.page.locator("main").get_by_text(f"{percent}%", exact=True).filter(visible=True).first

    def current_plan(self, plan_name: str):
        return self.page.locator("main").get_by_text(plan_name, exact=True).filter(visible=True).first

    # --- Buttons -----------------------------------------------------------

    # Nav item label -> its data-tour hook (University sits in the "more" slot).
    NAV_ITEMS = {
        "Home": "nav-home",
        "Manage Profile": "nav-manage-profile",
        "Physician Access": "nav-physician",
        "Pharmacy": "nav-pharmacy",
        "University": "nav-more",
        "Handbook": "nav-handbook",
    }

    def nav_link(self, label: str):
        item = self.page.locator(f"li[data-tour='{self.NAV_ITEMS[label]}']").filter(visible=True)
        return item.get_by_text(label, exact=True)

    def card(self, tour_key: str):
        """A dashboard card by its data-tour hook, e.g. "imaging" for data-tour="home-imaging"."""
        return self.page.locator(f"[data-tour='home-{tour_key}']").filter(visible=True)

    def card_button(self, tour_key: str, label: str):
        """The button labelled `label` inside a dashboard card ("Get Started" is on several cards)."""
        return self.card(tour_key).get_by_text(label, exact=True)

    def open_profile_menu(self):
        # Right after the dashboard loads, the avatar sometimes ignores the
        # first click, so click once more if the menu has not opened.
        for _ in range(2):
            self.profile_avatar.click()
            try:
                expect(self.profile_menu_item("myprofile")).to_have_count(1, timeout=5_000)
                return
            except AssertionError:
                pass
        raise AssertionError("The profile menu did not open from the avatar")

    def click_profile_menu_item(self, name: str):
        """Click a profile menu item by its data-tour name, e.g. "myprofile" or "logout".

        The dashboard re-renders shortly after loading, which can close the menu
        again, and the items scale on hover (never "stable"), so the item is
        clicked straight after opening the menu, retrying if the menu closed.
        """
        for _ in range(3):
            self.profile_avatar.click()
            try:
                self.profile_menu_item(name).click(force=True, timeout=5_000)
                return
            except Exception:
                pass
        raise AssertionError(f"Could not open the profile menu to click '{name}'")

    def open_my_profile(self):
        self.click_profile_menu_item("myprofile")

    def logout(self):
        self.click_profile_menu_item("logout")

    def accept_ai_doctor_terms(self):
        self.ai_doctor_terms_label.click()
        expect(self.ai_doctor_terms_checkbox).to_be_checked()

    def footer_link(self, label: str):
        return self.page.locator("main").get_by_role("link", name=label).filter(visible=True).first

    def open_popup(self, text: str):
        # Every popup stays in the page with opacity 0 when closed, so only an
        # opacity-100 container counts as open.
        return self.page.locator("div.fixed.opacity-100").filter(has_text=text)

    def close_popup(self, popup):
        """Close a popup with its red X icon (Peptide "Coming Soon", Impact)."""
        popup.locator("svg.lucide-x").click()
        expect(popup).to_have_count(0)

    # --- Going back between checks -------------------------------------------

    def back_to_dashboard(self, max_steps: int = 4):
        """Browser Back until the dashboard is shown again.

        Partner sites (pharmacy, telemedicine) log in through an extra page, so
        more than one Back can be needed.
        """
        for _ in range(max_steps):
            if self.URL_PATTERN.search(self.page.url):
                break
            self.page.go_back(wait_until="commit")
        if not self.is_showing(timeout=60_000):
            # Coming back from a partner site makes the portal reload its slow
            # 14 MB bundle; if it is still blank, load the dashboard directly.
            return self.open()
        return self

    def is_showing(self, timeout: float = 3_000) -> bool:
        """True when the dashboard is actually rendered (not just its URL on a blank page)."""
        if not self.URL_PATTERN.search(self.page.url):
            return False
        try:
            self.care_services_heading.wait_for(state="visible", timeout=timeout)
            return True
        except Exception:
            return False

    def reset(self):
        """Leave the shared tab on a clean dashboard, whatever the previous test left open."""
        for tab in self.page.context.pages:
            if tab != self.page:
                tab.close()
        # Only after a failed test is anything left over; reloading is then the safe way back.
        if not self.is_showing():
            return self.open()
        self.page.keyboard.press("Escape")  # closes menus, Handbook, Tour and the labs panel
        if self.page.locator("div.fixed.opacity-100").filter(visible=True).count():
            return self.open()  # a popup is still open
        return self

    def click_and_get_new_tab(self, locator) -> Page:
        with self.page.context.expect_page() as new_tab:
            locator.click()
        tab = new_tab.value
        tab.wait_for_load_state("domcontentloaded")
        return tab
