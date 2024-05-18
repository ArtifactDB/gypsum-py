import os
from datetime import datetime, timedelta, timezone

import pytest
from gypsum_client import (
    create_project,
    fetch_permissions,
    remove_project,
    set_permissions,
)

__author__ = "Jayaram Kancherla"
__copyright__ = "Jayaram Kancherla"
__license__ = "MIT"

app_url = "https://gypsum-test.artifactdb.com"


@pytest.mark.skipif(
    "gh_token" not in os.environ, reason="GitHub token not in environment"
)
def test_permission_setting():
    gh_token = os.environ.get("gh_token", None)
    if gh_token is None:
        raise ValueError("GitHub token not in environment")

    remove_project("test-Py-perms", token=gh_token, url=app_url)
    create_project("test-Py-perms", owners=["jkanche"], token=gh_token, url=app_url)

    until = (
        (datetime.now() + timedelta(seconds=1000000))
        .replace(microsecond=0)
        # .strftime("%Y-%m-%dT%H:%M:%S%Z")
    )

    set_permissions(
        "test-Py-perms",
        owners=["LTLA"],
        uploaders=[{"id": "lawremi", "until": until}],
        token=gh_token,
        url=app_url,
    )

    perms = fetch_permissions("test-Py-perms", url=app_url)
    assert sorted(perms["owners"]) == sorted(["LTLA", "jkanche"])
    assert len(perms["uploaders"]) == 1
    assert perms["uploaders"][0]["id"] == "lawremi"
    assert perms["uploaders"][0]["until"] == until

    # Checking uploader appending, while also checking owners=None.
    set_permissions(
        "test-Py-perms",
        uploaders=[{"id": "ArtifactDB-bot", "trusted": True}],
        token=gh_token,
        url=app_url,
    )
    perms = fetch_permissions("test-Py-perms", url=app_url)
    assert sorted(perms["owners"]) == sorted(["LTLA", "jkanche"])
    assert len(perms["uploaders"]) == 2
    assert perms["uploaders"][0]["id"] == "lawremi"
    assert perms["uploaders"][1]["id"] == "ArtifactDB-bot"
    assert perms["uploaders"][1]["trusted"] is True

    # Checking union of owners, and also that uploaders=None works.
    set_permissions(
        "test-Py-perms", owners=["PeteHaitch", "LTLA"], token=gh_token, url=app_url
    )
    perms = fetch_permissions("test-Py-perms", url=app_url)
    assert sorted(perms["owners"]) == sorted(["LTLA", "jkanche", "PeteHaitch"])
    assert len(perms["uploaders"]) == 2

    # Resetting the owners back.
    set_permissions(
        "test-Py-perms", owners=["jkanche"], append=False, token=gh_token, url=app_url
    )
    perms = fetch_permissions("test-Py-perms", url=app_url)
    assert perms["owners"] == ["jkanche"]
    assert len(perms["uploaders"]) == 2

    # Now resetting the uploaders.
    set_permissions(
        "test-Py-perms", uploaders=[], append=False, token=gh_token, url=app_url
    )
    perms = fetch_permissions("test-Py-perms", url=app_url)
    assert perms["owners"] == ["jkanche"]
    assert len(perms["uploaders"]) == 0
