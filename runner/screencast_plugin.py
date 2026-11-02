"""pytest plugin that streams every test browser page to the runner web page.

Loaded only by the runner (`pytest -p runner.screencast_plugin`), so normal
`pytest` runs are unaffected. It uses Chrome's built-in screencast (CDP
`Page.startScreencast`) and writes the latest JPEG frame, base64-encoded, to
the file named in RUNNER_FRAME_FILE. The runner server pushes that file to
the browser whenever it changes.
"""
import os

from playwright.sync_api import Browser

FRAME_FILE = os.environ.get("RUNNER_FRAME_FILE")

SCREENCAST_OPTIONS = {"format": "jpeg", "quality": 60, "maxWidth": 1280, "maxHeight": 800, "everyNthFrame": 1}


def _write_frame(data: str):
    tmp = FRAME_FILE + ".tmp"
    try:
        with open(tmp, "w") as f:
            f.write(data)
        os.replace(tmp, FRAME_FILE)
    except OSError:
        # The server may be reading the file at this moment; skip this frame.
        pass


def _start_screencast(page):
    try:
        session = page.context.new_cdp_session(page)
    except Exception:
        return

    def on_frame(params):
        _write_frame(params["data"])
        try:
            session.send("Page.screencastFrameAck", {"sessionId": params["sessionId"]})
        except Exception:
            pass

    session.on("Page.screencastFrame", on_frame)
    try:
        session.send("Page.startScreencast", SCREENCAST_OPTIONS)
    except Exception:
        pass


def _watch_context(context):
    context.on("page", _start_screencast)
    for page in context.pages:
        _start_screencast(page)


def pytest_configure(config):
    if not FRAME_FILE:
        return

    # Every browser context the tests create (pytest-playwright fixtures and
    # the e2e journey alike) goes through Browser.new_context.
    original_new_context = Browser.new_context

    def new_context(self, *args, **kwargs):
        context = original_new_context(self, *args, **kwargs)
        _watch_context(context)
        return context

    Browser.new_context = new_context
