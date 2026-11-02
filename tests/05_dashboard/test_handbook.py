"""Nav 'Handbook' opens the Member Handbook; Escape closes it."""
from playwright.sync_api import expect


def test_handbook_opens_member_handbook(dashboard):
    page = dashboard.page
    dashboard.nav_link("Handbook").click()
    guide = page.get_by_text("Your Benefits Guide").filter(visible=True).first
    expect(page.get_by_text("Member Handbook").filter(visible=True).first).to_be_visible()
    expect(guide).to_be_visible()
    print("\n  Handbook: 'Member Handbook' and 'Your Benefits Guide' shown")

    page.keyboard.press("Escape")
    expect(guide, "Handbook closed").to_be_hidden()
    print("  Escape -> Handbook closed")
