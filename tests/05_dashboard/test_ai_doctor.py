"""'Open My AI Doctor' opens the AI Doctor app on /ai; then the dashboard is opened again.

The first time in a browser, a terms popup comes first: 'OK, Continue' stays
disabled until the terms are ticked. The site remembers the choice in the
browser, so later it goes straight to /ai. Both cases are handled.
/ai shows the AI app (ai.optimalmd.com) in a frame; the member is signed in
automatically and the app can take ~45 s to load.
"""
import re

import pytest
from playwright.sync_api import expect


def test_ai_doctor_opens(dashboard):
    page = dashboard.page
    terms_popup = dashboard.open_popup("My AI Doctor™ — Before You Continue")
    dashboard.card_button("ai", "Open My AI Doctor™").click()

    # Either the terms popup or (terms accepted before) the AI page / error popup.
    first_screen = terms_popup.or_(dashboard.ai_doctor_frame).or_(dashboard.ai_doctor_error_popup)
    expect(first_screen.first).to_be_visible(timeout=60_000)
    if terms_popup.count():
        expect(dashboard.ai_doctor_continue_button).to_be_disabled()
        dashboard.accept_ai_doctor_terms()
        expect(dashboard.ai_doctor_continue_button).to_be_enabled()
        print("\n  Terms popup: 'OK, Continue' disabled until the terms are accepted")
        dashboard.ai_doctor_continue_button.click()
    else:
        print("\n  Terms already accepted in this browser, no popup")

    expect(dashboard.ai_doctor_frame.or_(dashboard.ai_doctor_error_popup).first).to_be_visible(timeout=60_000)
    if dashboard.ai_doctor_error_popup.count():
        # A system issue on the site's side, not a test problem: report it and fail.
        dashboard.ai_doctor_error_popup.get_by_role("button", name="OK").click()
        pytest.fail(
            "System issue: My AI Doctor did not open. The site showed 'Something Went Wrong — "
            "We couldn't open My AI Doctor™. Please try again in a moment.'",
            pytrace=False,
        )
    expect(page).to_have_url(re.compile(r"/ai$"))
    expect(dashboard.ai_doctor_app, "AI Doctor app loaded ('Back to Portal' in its header)").to_be_visible(timeout=120_000)
    print(f"  'Open My AI Doctor' opened {page.url}: the AI Doctor app loaded and signed the member in")

    # The AI frame adds its own history entries, so browser Back stays on /ai: open the dashboard instead.
    dashboard.open()
    print("  Dashboard opened again")
