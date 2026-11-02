"""Shared fixtures and hooks for every test folder.

Sections:
  0. Feature tour            - skipped automatically whenever it pops up
  1. Saved member session    - one logged-in tab shared by login, profile, dashboard,
                               dependents and change password (logged in once per run)
  2. Ordered journeys        - one browser shared by ordered steps (e2e, registration)
  3. Dependents              - the saved Prime member the dependents are added to
  4. Failure screenshots     - for tests that use their own browser contexts

The full flow (every folder except e2e) runs in folder order: registration saves a
new member -> login -> profile activation -> dashboard -> dependents, all in the
saved member's one browser tab.
"""
from pathlib import Path

import pytest
from playwright.sync_api import Browser

from pages.dashboard_page import DashboardPage
from pages.login_page import LoginPage
from pages.update_profile_page import UpdateProfilePage
from utils.email_reader import get_login_credentials
from utils.member_store import load_latest_member, update_latest_member
from utils.test_data import new_profile_details

SCREENSHOT_DIR = Path("test-results")
MAX_DEPENDENTS = 7  # Prime plan limit
NEW_DEPENDENTS = 2  # one adult, one child per dependents run


# --- 0. Feature tour ---------------------------------------------------------
# The dashboard's "Feature Spotlight" tour can open at any moment after a page
# loads and covers whatever the test wants to click. A locator handler clicks
# "Skip tour" whenever the tour is on screen before Playwright acts or asserts.
# Every browser context in every test is created through Browser.new_context,
# so the handler is added there for each new page.

def _skip_tour_whenever_shown(page):
    skip_tour = page.locator("button.omd-tour-skip-link")
    page.add_locator_handler(skip_tour, lambda: skip_tour.click())


def pytest_configure(config):
    original_new_context = Browser.new_context

    def new_context(self, *args, **kwargs):
        context = original_new_context(self, *args, **kwargs)
        context.on("page", _skip_tour_whenever_shown)
        return context

    Browser.new_context = new_context


# --- 1. Saved member session -------------------------------------------------
# The latest member saved by the registration (or e2e) tests, in one browser tab
# for the whole run. The file is read when the first test needs it, so in a full
# run it is the member the registration tests just created. The login test logs
# in; tests that run without it (a folder or file on its own) log in here instead.

@pytest.fixture(scope="session")
def member_session(browser, base_url):
    member = load_latest_member()
    if not member:
        pytest.skip("No saved member yet. Run the registration (or e2e) tests first.")
    full_name = f"{member['first_name']} {member['last_name']}"
    print(f"\n  Saved member: {full_name} <{member['email']}> ({member['plan']}, registered {member['registered_at']})")

    if not member["password"]:
        print("  Password not saved yet. Reading it from the credentials email...")
        member["password"] = get_login_credentials(member["email"])["password"]
        update_latest_member(password=member["password"])

    context = browser.new_context(base_url=base_url)
    page = context.new_page()
    page.set_default_timeout(30_000)
    yield {"member": member, "full_name": full_name, "page": page, "logged_in": False}
    context.close()


def log_in(session):
    """Log the shared tab in with the saved member's credentials (once per run)."""
    if session["logged_in"]:
        return
    member = session["member"]
    LoginPage(session["page"]).open().login(member["email"], member["password"])
    DashboardPage(session["page"]).wait_until_loaded()
    session["logged_in"] = True
    print(f"  Logged in as {session['full_name']}")


def activate_if_needed(session):
    """Activate the member's profile when the profile tests have not done it yet (no saved address)."""
    member = session["member"]
    if member["address"]:
        return
    page = session["page"]
    details = new_profile_details()
    dashboard = DashboardPage(page)
    if not dashboard.is_showing():
        dashboard.open()
    dashboard.start_profile_completion()
    profile = UpdateProfilePage(page).wait_until_loaded()
    profile.complete_personal_demographics(details["gender"])
    profile.complete_contact_information(details["address"])
    profile.continue_from_payment()
    profile.activate()
    profile.close_updated_popup()
    dashboard.wait_until_loaded()
    member["address"] = details["address"]
    update_latest_member(address=member["address"])
    print("  Member profile was not activated yet, activated it now")


@pytest.fixture
def logged_in_member(member_session):
    """The shared tab, logged in."""
    log_in(member_session)
    return member_session


@pytest.fixture
def dashboard(logged_in_member) -> DashboardPage:
    """The shared tab on a clean dashboard: each dashboard test clicks one button,
    checks the result and goes back. Anything a failed test left open is reset."""
    activate_if_needed(logged_in_member)
    return DashboardPage(logged_in_member["page"]).reset()


# --- 2. Ordered journeys -----------------------------------------------------
# A flow is split into ordered steps (one test each) that share one browser, so
# the report shows exactly which step passed or failed without reloading pages
# between steps. When a step fails, the rest are skipped.
# A journey is one test file, unless its files set the same JOURNEY name: the
# e2e steps are one file each (test_01_..., test_02_...) and share one journey.

class JourneyState(dict):
    def __missing__(self, key):
        # A step file run on its own has none of the earlier steps' results.
        pytest.skip(f"Needs '{key}' from an earlier step. Run the whole folder.")


@pytest.fixture(scope="session")
def _journeys(browser, base_url):
    journeys = {}

    def start(name):
        # Steps run one journey at a time, so the previous journey's browsers can close.
        for state in journeys.values():
            for context in state["contexts"]:
                context.close()
            state["contexts"].clear()

        state = JourneyState(base_url=base_url, contexts=[], failed_step=None)

        def new_page():
            """Open a fresh browser (new session) and make it the journey's current page."""
            context = browser.new_context(base_url=base_url)
            state["contexts"].append(context)
            page = context.new_page()
            page.set_default_timeout(30_000)
            state["page"] = page
            return page

        state["new_page"] = new_page
        journeys[name] = state
        return state

    yield journeys, start
    for state in journeys.values():
        for context in state["contexts"]:
            context.close()


@pytest.fixture
def journey(request, _journeys):
    journeys, start = _journeys
    name = getattr(request.module, "JOURNEY", request.module.__name__)
    return journeys.get(name) or start(name)


@pytest.fixture(autouse=True)
def skip_after_failed_step(request):
    if "journey" not in request.fixturenames:
        return
    failed_step = request.getfixturevalue("journey")["failed_step"]
    if failed_step:
        pytest.skip(f"Skipped because an earlier step failed: {failed_step}")


# --- 3. Dependents -----------------------------------------------------------
# Dependents are added to the saved Prime member in the shared tab. Only the
# dependent's own login opens a separate browser.

@pytest.fixture(scope="module")
def prime_member(browser, base_url, member_session):
    log_in(member_session)
    activate_if_needed(member_session)
    contexts = []

    def new_page():
        context = browser.new_context(base_url=base_url)
        contexts.append(context)
        page = context.new_page()
        page.set_default_timeout(30_000)
        return page

    page = member_session["page"]
    profile = UpdateProfilePage(page).open()
    existing = profile.dependent_count()
    removed = profile.remove_unfinished_dependents()
    if removed:
        existing -= removed
        print(f"  Removed {removed} unfinished dependent(s) left by an earlier failed run")
    print(f"  Member already has {existing} of {MAX_DEPENDENTS} dependents")
    if existing + NEW_DEPENDENTS > MAX_DEPENDENTS:
        pytest.skip(
            f"{member_session['full_name']} already has {existing} dependents and Prime allows {MAX_DEPENDENTS}. "
            "Run the registration tests to create a fresh member."
        )

    yield {
        "page": page,
        "full_name": member_session["full_name"],
        "address": member_session["member"]["address"],
        # A member has at most one spouse, so a second run adds an "Other" adult instead.
        "adult_relation": "Other" if profile.dependent_cards.filter(has_text="(Spouse)").count() else "Spouse",
        "new_page": new_page,
        "contexts": contexts,
        "dependents": {},  # "adult" / "child" -> dependent dict, filled as dependents are activated
    }
    for context in contexts:
        context.close()


@pytest.fixture
def member_profile(prime_member) -> UpdateProfilePage:
    """The saved member's Manage Profile page, freshly loaded."""
    return UpdateProfilePage(prime_member["page"]).open()


# --- 4. Failure screenshots --------------------------------------------------
# pytest-playwright screenshots its own `page` fixture. The journey, shared-tab
# and dependents tests open their own browser contexts, so their screenshots
# are taken here, under test-results/<test folder>/.

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    if report.when != "call" or not report.failed or not hasattr(item, "funcargs"):
        return

    journey = item.funcargs.get("journey")
    if journey is not None:
        journey["failed_step"] = item.name
        pages = [journey["page"]] if journey.get("page") else []
    else:
        pages = []
        if item.funcargs.get("member_session"):
            pages += item.funcargs["member_session"]["page"].context.pages
        if item.funcargs.get("prime_member"):
            pages += [p for context in item.funcargs["prime_member"]["contexts"] for p in context.pages]
        if not pages:
            return

    folder = item.path.parent.name  # e.g. "01_e2e"
    for i, page in enumerate(pages):
        if page.is_closed():
            continue
        path = SCREENSHOT_DIR / folder / f"{item.name}-{i}.png"
        path.parent.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(path), full_page=True)
        print(f"\n  Screenshot of the failure: {path}")
