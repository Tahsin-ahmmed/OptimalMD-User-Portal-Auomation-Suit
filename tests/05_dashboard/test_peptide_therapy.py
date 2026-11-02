"""'Peptide Therapy' -> 'Get Started' opens the 'Coming Soon' popup; its X closes it."""
from playwright.sync_api import expect


def test_peptide_therapy_opens_popup(dashboard):
    popup = dashboard.open_popup("Coming Soon")
    expect(popup).to_have_count(0)
    dashboard.card_button("peptide", "Get Started").click()
    expect(popup).to_be_visible()
    print("\n  'Peptide Therapy' -> 'Coming Soon' popup shown")

    dashboard.close_popup(popup)
    print("  X -> popup closed")
