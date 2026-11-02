import email
import html
import imaplib
import os
import re
import time

from dotenv import load_dotenv

load_dotenv()

IMAP_HOST = "imap.gmail.com"
# Gmail sometimes files the credentials email under Spam.
MAILBOXES = ["INBOX", '"[Gmail]/Spam"']


def _connect():
    mail = imaplib.IMAP4_SSL(IMAP_HOST)
    mail.login(os.environ["GMAIL_ADDRESS"], os.environ["GMAIL_APP_PASSWORD"])
    return mail


def _email_html(message) -> str:
    for part in message.walk():
        if part.get_content_type() == "text/html":
            payload = part.get_payload(decode=True) or b""
            return payload.decode(part.get_content_charset() or "utf-8", "replace")
    return ""


def _email_text(message) -> str:
    """Return the email body as plain text (HTML tags stripped)."""
    parts = []
    for part in message.walk():
        if part.get_content_type() in ("text/plain", "text/html"):
            payload = part.get_payload(decode=True) or b""
            parts.append(payload.decode(part.get_content_charset() or "utf-8", "replace"))
    text = re.sub(r"<[^>]+>", " ", " ".join(parts))
    return text.replace("&nbsp;", " ")


MEMBER_SUBJECT = "New Member Credentials"
DEPENDENT_SUBJECT = "Registered as Dependent"


def get_login_credentials(to_address: str, subject: str = MEMBER_SUBJECT, timeout: int = 300, poll_interval: int = 5) -> dict:
    """Wait for the credentials email sent to to_address and return its username and password.

    Members get "New Member Credentials" (Username: ...); dependents get
    "Welcome to OptimalMD | Registered as Dependent" (Email: ...).
    """
    mail = imaplib.IMAP4_SSL(IMAP_HOST)
    mail.login(os.environ["GMAIL_ADDRESS"], os.environ["GMAIL_APP_PASSWORD"])
    try:
        deadline = time.time() + timeout
        while time.time() < deadline:
            for mailbox in MAILBOXES:
                mail.select(mailbox, readonly=True)
                _, ids = mail.search(None, f'(TO "{to_address}" SUBJECT "{subject}")')
                if ids[0]:
                    _, data = mail.fetch(ids[0].split()[-1], "(BODY.PEEK[])")
                    text = _email_text(email.message_from_bytes(data[0][1]))
                    username = re.search(r"(?:Username|Email):\s*(\S+@\S+)", text)
                    password = re.search(r"Password:\s*(\S+)", text)
                    if username and password:
                        return {"username": username.group(1), "password": password.group(1)}
            time.sleep(poll_interval)
        raise TimeoutError(f"No credentials email for {to_address} within {timeout}s")
    finally:
        mail.logout()


# --- Password reset ---------------------------------------------------------
# Every reset sends new emails with the same subjects, so the caller first takes
# a snapshot of the emails already there and then waits for one that is new.

RESET_CODE_SUBJECT = "Password Reset Verification code"
RESET_LINK_SUBJECT = "Complete Your Password Reset"


def _uids(mail, to_address: str, subject: str) -> set:
    uids = set()
    for mailbox in MAILBOXES:
        mail.select(mailbox, readonly=True)
        _, data = mail.uid("search", None, f'(TO "{to_address}" SUBJECT "{subject}")')
        uids |= {(mailbox, uid) for uid in data[0].split()}
    return uids


def existing_emails(to_address: str, subject: str) -> set:
    """Snapshot of the matching emails already received (take it before triggering a new one)."""
    mail = _connect()
    try:
        return _uids(mail, to_address, subject)
    finally:
        mail.logout()


def wait_for_new_email(to_address: str, subject: str, seen: set, timeout: int = 300, poll_interval: int = 5):
    """Wait for an email that is not in `seen` and return it."""
    mail = _connect()
    try:
        deadline = time.time() + timeout
        while time.time() < deadline:
            new = _uids(mail, to_address, subject) - seen
            if new:
                mailbox, uid = max(new, key=lambda item: int(item[1]))
                mail.select(mailbox, readonly=True)
                _, data = mail.uid("fetch", uid, "(BODY.PEEK[])")
                return email.message_from_bytes(data[0][1])
            time.sleep(poll_interval)
        raise TimeoutError(f"No new '{subject}' email for {to_address} within {timeout}s")
    finally:
        mail.logout()


def get_reset_code(to_address: str, seen: set, timeout: int = 300) -> str:
    """The 6-digit code from a new "Password Reset Verification code" email."""
    text = html.unescape(_email_text(wait_for_new_email(to_address, RESET_CODE_SUBJECT, seen, timeout)))
    match = re.search(r"verification code below to proceed:\s*(\d{6})", text)
    if not match:
        raise AssertionError("Password reset code email has no 6-digit code")
    return match.group(1)


def get_reset_link(to_address: str, seen: set, timeout: int = 300) -> str:
    """The link behind the "Create New Password" button in a new "Complete Your Password Reset" email."""
    body = _email_html(wait_for_new_email(to_address, RESET_LINK_SUBJECT, seen, timeout))
    for href, label in re.findall(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', body, flags=re.S | re.I):
        if "create new password" in re.sub(r"<[^>]+>|\s+", " ", label).lower():
            return html.unescape(href)
    raise AssertionError("Password reset email has no 'Create New Password' link")
