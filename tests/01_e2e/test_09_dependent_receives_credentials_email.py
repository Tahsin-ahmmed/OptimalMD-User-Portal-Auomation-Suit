"""E2E step 9: the adult dependent receives the "Registered as Dependent" email with their login credentials."""
import re

import pytest

from utils.email_reader import DEPENDENT_SUBJECT, get_login_credentials

pytestmark = pytest.mark.e2e
JOURNEY = "new_member"


def test_step9_dependent_receives_credentials_email(journey):
    email = journey["dependent"]["email"]
    credentials = get_login_credentials(email, DEPENDENT_SUBJECT)
    journey["dependent_credentials"] = credentials
    print(f"\n  'Registered as Dependent' email received: username={credentials['username']} password={credentials['password']}")

    assert credentials["username"] == email, (
        f"Email in the credentials email ({credentials['username']}) does not match the dependent's ({email})"
    )
    assert re.fullmatch(r"\S{6,}", credentials["password"]), "Temporary password in email looks invalid"
