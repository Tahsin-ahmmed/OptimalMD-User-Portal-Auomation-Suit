"""Remembers the latest Prime member registered by the e2e or referral-code registration tests.

The dependents tests log in as this member instead of registering their own.
Each new Prime registration replaces it. The file is local test data only.
"""
import json
from datetime import datetime
from pathlib import Path

STATE_FILE = Path(__file__).resolve().parent.parent / "test_state" / "latest_member.json"


def save_latest_member(member: dict, plan: str):
    """Start a new record right after registration (password and address come later)."""
    record = {
        "email": member["email"],
        "first_name": member["first_name"],
        "last_name": member["last_name"],
        "phone": member["phone"],  # phone and date of birth: the profile test checks they are pre-filled
        "dob": member["dob"],
        "plan": plan,
        "password": None,  # filled once the credentials email is read
        "address": None,  # filled once the profile is activated
        "registered_at": datetime.now().isoformat(timespec="seconds"),
    }
    _write(record)


def update_latest_member(**fields):
    record = load_latest_member()
    if record:
        record.update(fields)
        _write(record)


def load_latest_member():
    if not STATE_FILE.exists():
        return None
    return json.loads(STATE_FILE.read_text(encoding="utf-8"))


def _write(record: dict):
    STATE_FILE.parent.mkdir(exist_ok=True)
    STATE_FILE.write_text(json.dumps(record, indent=2), encoding="utf-8")
