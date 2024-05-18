import os
import tempfile
from pathlib import Path

import pytest
from gypsum_client import (
    create_project,
    fetch_quota,
    fetch_usage,
    refresh_usage,
    remove_project,
    set_quota,
)

__author__ = "Jayaram Kancherla"
__copyright__ = "Jayaram Kancherla"
__license__ = "MIT"

blah_contents = (
    "A\nB\nC\nD\nE\nF\nG\nH\nI\nJ\nK\nL\nM\nN\nO\nP\nQ\nR\nS\nT\nU\nV\nW\nX\nY\nZ\n"
)
foobar_contents = "1 2 3 4 5\n6 7 8 9 10\n"

app_url = "https://gypsum-test.artifactdb.com"


@pytest.mark.skipif(
    "gh_token" not in os.environ, reason="GitHub token not in environment"
)
def test_quota():
    gh_token = os.environ.get("gh_token", None)
    if gh_token is None:
        raise ValueError("GitHub token not in environment")

    remove_project("test-Py-quota", token=gh_token, url=app_url)
    create_project("test-Py-quota", owners=["jkanche"], token=gh_token, url=app_url)

    set_quota(
        "test-Py-quota",
        baseline=1234,
        growth_rate=5678,
        year=2020,
        token=gh_token,
        url=app_url,
    )

    quot = fetch_quota("test-Py-quota", url=app_url)
    assert quot["baseline"] == 1234
    assert quot["growth_rate"] == 5678
    assert quot["year"] == 2020


@pytest.mark.skipif(
    "gh_token" not in os.environ, reason="GitHub token not in environment"
)
def test_usage():
    gh_token = os.environ.get("gh_token", None)
    if gh_token is None:
        raise ValueError("GitHub token not in environment")

    remove_project("test-Py-quota", token=gh_token, url=app_url)
    create_project("test-Py-quota", owners=["jkanche"], token=gh_token, url=app_url)

    # Fetch the initial usage
    initial_usage = fetch_usage("test-Py-quota", url=app_url)
    assert initial_usage == 0

    # Refresh the usage and check
    refreshed_usage = refresh_usage("test-Py-quota", url=app_url)
    assert refreshed_usage == 0
