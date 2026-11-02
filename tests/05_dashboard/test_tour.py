"""Nav 'Tour' opens the tour menu; Escape closes it."""
from playwright.sync_api import expect


def test_tour_opens_tour_menu(dashboard):
    page = dashboard.page
    dashboard.tour_button.click()
    start_tour = page.get_by_text("Start Full Tour").filter(visible=True).first
    expect(start_tour).to_be_visible()
    print("\n  Tour: menu with 'Start Full Tour' shown")

    page.keyboard.press("Escape")
    expect(start_tour, "Tour menu closed").to_be_hidden()
    print("  Escape -> tour menu closed")
