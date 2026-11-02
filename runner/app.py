"""Web page that runs the pytest suites with live output and a live browser view.

Start:  venv\\Scripts\\python.exe -m runner.app   (or double-click start_runner.bat)
Open:   http://localhost:5000

Environment (all optional):
  RUNNER_HOST       interface to listen on (default 127.0.0.1)
  RUNNER_PORT       port (default 5000)
  RUNNER_HEADLESS   "1" to run Chrome without a window (for servers)
  RUNNER_PASSWORD   if set, the page asks for this password (HTTP Basic auth)
"""
import json
import os
import re
import signal
import subprocess
import sys
import tempfile
import threading
import time
from functools import wraps
from pathlib import Path

from flask import Flask, Response, jsonify, render_template, request

ROOT = Path(__file__).resolve().parent.parent
TESTS_DIR = ROOT / "tests"
FRAME_FILE = Path(tempfile.gettempdir()) / "optimalmd_runner_frame.b64"
HEADLESS = os.getenv("RUNNER_HEADLESS") == "1"
PASSWORD = os.getenv("RUNNER_PASSWORD")


app = Flask(__name__)


class RunState:
    def __init__(self):
        self.lock = threading.Lock()
        self.process = None
        self.run_id = 0
        self.label = ""
        self.lines = []
        self.running = False
        self.exit_code = None
        self.started_at = None

    def status(self) -> dict:
        return {
            "run_id": self.run_id,
            "label": self.label,
            "running": self.running,
            "exit_code": self.exit_code,
            "started_at": self.started_at,
        }


state = RunState()


# --- Test discovery -------------------------------------------------------

def suite_label(folder: str) -> str:
    # "01_e2e" -> "E2E", "06_dependents" -> "Dependents", "07_password_change" -> "Password change"
    name = re.sub(r"^\d+_", "", folder)
    return name.upper() if name == "e2e" else name.replace("_", " ").capitalize()


# "Full flow": every folder except these, in folder order (registration -> login ->
# profile -> dashboard -> dependents), all on the member the registration tests save.
# Password change is left out for now; remove it from this list to include it.
FULL_FLOW_TARGET = "full-flow"
FULL_FLOW_EXCLUDES = ["tests/01_e2e", "tests/07_password_change"]


def discover_suites() -> list:
    """One entry per folder in tests/ that contains test files, plus 'Full flow'.

    Folders are numbered (01_e2e, 02_registration, ...) so sorting by name gives the run order.
    """
    folders = sorted(d.name for d in TESTS_DIR.iterdir() if d.is_dir() and any(d.rglob("test_*.py")))
    suites = [{"label": suite_label(name), "target": f"tests/{name}"} for name in folders]
    suites.append({"label": "Full flow", "target": FULL_FLOW_TARGET})
    return suites


def discover_files() -> list:
    return sorted(str(p.relative_to(ROOT)).replace("\\", "/") for p in TESTS_DIR.rglob("test_*.py"))


def allowed_targets() -> set:
    return {s["target"] for s in discover_suites()} | set(discover_files())


# --- Running pytest -------------------------------------------------------

def pytest_command(target: str, show_browser: bool = False, slow_motion: bool = False) -> list:
    # Headless and full speed by default (the live view still shows the browser);
    # the page's checkboxes open a real window and/or slow every action down to watch it.
    options = [
        "-o", "addopts=",
        "-v", "-s", "-rA",
        "--browser", "chromium",
        "--screenshot", "only-on-failure",
        "--output", "test-results",
        "-p", "runner.screencast_plugin",
        "-p", "no:cacheprovider",
        "-W", "ignore::DeprecationWarning",
    ]
    if show_browser and not HEADLESS:
        options.append("--headed")
    if slow_motion:
        options += ["--slowmo", "300"]
    if target == FULL_FLOW_TARGET:
        paths = ["tests", *(f"--ignore={folder}" for folder in FULL_FLOW_EXCLUDES)]
    else:
        paths = [target]
    return [sys.executable, "-u", "-m", "pytest", *paths, *options]


def read_output(process, run_id):
    for raw in process.stdout:
        line = raw.rstrip("\r\n")
        with state.lock:
            if state.run_id == run_id:
                state.lines.append(line)
    code = process.wait()
    with state.lock:
        if state.run_id == run_id:
            state.running = False
            state.exit_code = code
            state.process = None


def kill_process_tree(process):
    if os.name == "nt":
        subprocess.run(["taskkill", "/T", "/F", "/PID", str(process.pid)], capture_output=True)
    else:
        os.killpg(os.getpgid(process.pid), signal.SIGTERM)


# --- Optional password ----------------------------------------------------

def password_protected(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if PASSWORD:
            auth = request.authorization
            if not auth or auth.password != PASSWORD:
                return Response("Password required", 401, {"WWW-Authenticate": 'Basic realm="Test Runner"'})
        return view(*args, **kwargs)
    return wrapper


# --- Routes ---------------------------------------------------------------

@app.get("/")
@password_protected
def index():
    return render_template("index.html", suites=discover_suites(), files=discover_files(), headless=HEADLESS)


@app.post("/run")
@password_protected
def run():
    body = request.get_json(silent=True) or {}
    target = body.get("target", "")
    if target not in allowed_targets():
        return jsonify(error=f"Unknown test target: {target}"), 400

    with state.lock:
        if state.running:
            return jsonify(error="A run is already in progress"), 409
        FRAME_FILE.unlink(missing_ok=True)
        env = {
            **os.environ,
            "RUNNER_FRAME_FILE": str(FRAME_FILE),
            "PYTHONIOENCODING": "utf-8",
            "PYTHONUNBUFFERED": "1",
        }
        command = pytest_command(target, bool(body.get("show_browser")), bool(body.get("slow_motion")))
        process = subprocess.Popen(
            command,
            cwd=ROOT,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            start_new_session=(os.name != "nt"),
        )
        state.run_id += 1
        state.process = process
        state.label = target
        state.lines = [f"$ pytest {target}", ""]
        state.running = True
        state.exit_code = None
        state.started_at = time.time()
        run_id = state.run_id

    threading.Thread(target=read_output, args=(process, run_id), daemon=True).start()
    return jsonify(state.status())


@app.post("/stop")
@password_protected
def stop():
    with state.lock:
        process = state.process
        if not (state.running and process):
            return jsonify(error="Nothing is running"), 409
        state.lines.append("")
        state.lines.append("■ Run stopped by user")
    kill_process_tree(process)
    return jsonify(ok=True)


@app.get("/stream")
@password_protected
def stream():
    """Server-Sent Events: log lines, run status and live browser frames."""

    def events():
        seen_run, cursor, last_status, last_frame_mtime, last_ping = None, 0, None, 0.0, 0.0
        while True:
            with state.lock:
                status = state.status()
                if status["run_id"] != seen_run:
                    seen_run, cursor = status["run_id"], 0
                    yield "event: reset\ndata: {}\n\n"
                new_lines = state.lines[cursor:]
                cursor += len(new_lines)

            for line in new_lines:
                yield f"event: log\ndata: {json.dumps(line)}\n\n"

            if status != last_status:
                last_status = status
                yield f"event: status\ndata: {json.dumps(status)}\n\n"

            try:
                mtime = FRAME_FILE.stat().st_mtime
                if mtime != last_frame_mtime:
                    frame = FRAME_FILE.read_text()
                    last_frame_mtime = mtime
                    if frame:
                        yield f"event: frame\ndata: {frame}\n\n"
            except OSError:
                pass

            now = time.time()
            if now - last_ping > 15:
                last_ping = now
                yield ": ping\n\n"
            time.sleep(0.1)

    return Response(events(), mimetype="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


if __name__ == "__main__":
    host = os.getenv("RUNNER_HOST", "127.0.0.1")
    port = int(os.getenv("RUNNER_PORT", "5000"))
    print(f"Test runner on http://{'localhost' if host == '127.0.0.1' else host}:{port}  (headless={HEADLESS})")
    app.run(host=host, port=port, threaded=True, debug=False)
