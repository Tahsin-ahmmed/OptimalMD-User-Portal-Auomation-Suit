"""'Major Health Events' -> 'Enroll Now' opens the 'Join Impact Health Sharing' popup; its X closes it."""
from playwright.sync_api import expect


def test_impact_health_sharing_opens_popup(dashboard):
    popup = dashboard.open_popup("Join Impact Health Sharing")
    expect(popup).to_have_count(0)
    dashboard.card_button("impact", "Enroll Now").click()
    expect(popup).to_be_visible()
    print("\n  'Major Health Events' -> 'Join Impact Health Sharing' popup shown")

    dashboard.close_popup(popup)
    print("  X -> popup closed")
