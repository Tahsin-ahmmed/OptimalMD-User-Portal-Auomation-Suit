# OptimalMD Member Portal — Test Automation Suite

End-to-end UI test automation for a healthcare membership portal (staging), built with
**Python, Playwright and pytest** using the **Page Object Model**. It covers the full member
lifecycle — registration with Stripe test payments and referral coupons, emailed login
credentials, profile activation, dashboard services, dependents and password change — and
ships with a small web runner that shows a **live browser view** and **readable step-by-step
results**.

## Highlights

- **Real end-to-end flows, including email.** Login credentials, dependent invitations and
  6-digit verification codes are read from a Gmail inbox over IMAP, so the tests do exactly
  what a member does: register, open the email, log in.
- **Page Object Model.** Every page and popup lives in `pages/`; tests only describe the flow.
- **Ordered step tests.** Long flows are split into steps (one test each) that share one
  browser; the report shows exactly which step broke, and the later steps are skipped.
- **One login per run.** Login, profile, dashboard and dependents tests share one logged-in
  browser tab, so the full flow does not log in or reload between tests.
- **Built for a slow, changing staging site.** Waits on real UI state (no fixed sleeps),
  auto-dismisses the feature-tour overlay whenever it appears, handles hidden duplicate
  menus/popups, and resets the dashboard after a failed test.
- **Stable locators.** `data-tour` hooks, `name` attributes, ARIA roles and labels first;
  text and structure only where the site offers nothing better.
- **Clear failures.** Automatic full-page screenshots in `test-results/<folder>/`, and site
  outages (e.g. "Something Went Wrong") are reported as system issues.
- **Web runner.** One click per suite, live browser screencast (also when headless),
  readable or raw output, optional visible window and slow motion.

## Tech stack

Python 3.12 · Playwright · pytest · pytest-playwright · Flask (runner) · IMAP (Gmail) · Faker

## Project structure

```
pages/                    Page objects (login, registration, dashboard, profile, my profile,
                          change / forgot / reset password, welcome)
tests/
  conftest.py             Shared fixtures: tour handler, shared logged-in session,
                          ordered journeys, dependents, failure screenshots
  01_e2e/                 New member -> activate -> add dependent -> dependent logs in (11 steps)
  02_registration/        Page checks, plan prices, Individual plan, referral coupon
  03_login/               Login with the saved member
  04_profile/             Profile activation wizard
  05_dashboard/           One file per dashboard button / service (19)
  06_dependents/          Add adult + child dependent, dependent login
  07_password_change/     Change password (code by email); forgot password
utils/
  email_reader.py         Gmail IMAP: credentials, verification codes, reset links
  member_store.py         Saves the latest registered member for the next suites
  test_data.py            Random members, dependents, addresses, Stripe test cards
runner/                   Flask web runner with live screencast
```

## Test flows

**Full flow** (every folder except E2E) runs on the member that registration creates:

```
Registration (save member) -> Login -> Profile activation -> Dashboard -> Dependents
```

**E2E** is a self-contained journey: register -> credentials email -> login -> activate ->
My Profile services -> add adult dependent -> member logs out -> dependent's email ->
dependent logs in -> dependent's My Profile.

## Setup

```bash
python -m venv venv
venv\Scripts\activate            # macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
playwright install chromium
copy .env.example .env           # then fill in the Gmail address and app password
```

## Running

**Web runner** (recommended): double-click `start_runner.bat`, or

```bash
python -m runner.app             # http://localhost:5000
```

**Command line:**

```bash
pytest tests/01_e2e                                              # E2E journey
pytest tests --ignore=tests/01_e2e --ignore=tests/07_password_change   # full flow
pytest tests/05_dashboard                                        # one suite
pytest tests/05_dashboard/test_pharmacy.py                       # one test
```

Runs are headless and at full speed by default. To watch one, tick **Show browser window**
and/or **Slow motion** in the runner, or add `--headed --slowmo 300` on the command line.

Run a whole folder for ordered flows: a step file run on its own skips with
"Run the whole folder".

## Known site issues (tests report them, they are not test bugs)

- **My AI Doctor:** staging sometimes shows "Something Went Wrong — We couldn't open My AI Doctor™".
- **Forgot password:** skipped until a staging bug is fixed (the reset API answers "Email not found").
- **Physician Access:** the test expects the geo-restriction message shown outside the USA.
