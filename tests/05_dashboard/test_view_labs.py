"""Lab Tests -> 'View Labs' opens the lab panel; Escape closes it."""
from playwright.sync_api import expect


def test_view_labs_opens_lab_panel(dashboard):
    page = dashboard.page
    dashboard.card_button("lab", "View Labs").click()
    lab_frame = page.locator("iframe[src*='medications?tab=lab']")
    expect(page.get_by_text("Back", exact=True).filter(visible=True).first).to_be_visible()
    expect(lab_frame).to_be_visible()
    print("\n  View Labs: lab panel shown")

    page.keyboard.press("Escape")
    expect(lab_frame, "Lab panel closed").to_be_hidden()
    print("  Escape -> lab panel closed")
