"""The language button lists Spanish; clicking it again closes the menu."""
from playwright.sync_api import expect


def test_language_menu_lists_spanish(dashboard):
    dashboard.language_button.click()
    spanish = dashboard.page.get_by_text("Español", exact=True).filter(visible=True).first
    expect(spanish).to_be_visible()
    print("\n  Language menu: 'Español' listed")

    dashboard.language_button.click()
    expect(spanish, "Language menu closed").to_be_hidden()
    print("  Language button again -> menu closed")
