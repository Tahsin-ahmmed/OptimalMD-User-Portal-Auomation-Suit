"""The profile avatar opens the profile menu; clicking it again closes the menu."""
from playwright.sync_api import expect


def test_profile_avatar_opens_profile_menu(dashboard):
    dashboard.open_profile_menu()
    page = dashboard.page
    for item in ["Edit Profile", "My Profile", "Change Password"]:
        expect(page.get_by_text(item, exact=True).filter(visible=True).first).to_be_visible()
    print("\n  Profile menu: Edit Profile, My Profile, Change Password shown")

    dashboard.profile_avatar.click()
    expect(dashboard.profile_menu_item("myprofile"), "Profile menu closed").to_have_count(0)
    print("  Avatar again -> profile menu closed")
