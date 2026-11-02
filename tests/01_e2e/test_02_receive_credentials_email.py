"""E2E step 2: the member receives the "New Member Credentials" email with a username and temporary password."""
import re

import pytest

from utils.email_reader import get_login_credentials
from utils.member_store import update_latest_member

pytestmark = pytest.mark.e2e
JOURNEY = "new_member"


def test_step2_receive_credentials_email(journey):
    email = journey["member"]["email"]
    credentials = get_login_credentials(email)
    journey["credentials"] = credentials
    update_latest_member(password=credentials["password"])
    print(f"\n  Credentials email received: username={credentials['username']} password={credentials['password']}")

    assert credentials["username"] == email, (
        f"Username in email ({credentials['username']}) does not match registered email ({email})"
    )
    assert re.fullmatch(r"\S{6,}", credentials["password"]), "Temporary password in email looks invalid"
