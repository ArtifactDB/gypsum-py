import os

import pytest
from gypsum_client import fetch_latest, refresh_latest

__author__ = "Jayaram Kancherla"
__copyright__ = "Jayaram Kancherla"
__license__ = "MIT"

app_url = "https://gypsum-test.artifactdb.com"


@pytest.mark.skipif(
    "gh_token" not in os.environ, reason="GitHub token not in environment"
)
def test_refresh_latest():
    gh_token = os.environ.get("gh_token", None)
    if gh_token is None:
        raise ValueError("GitHub token not in environment")

    ver = refresh_latest("test-R", "basic", url=app_url, token=gh_token)
    assert ver == "v3"
    assert fetch_latest("test-R", "basic", url=app_url) == ver
