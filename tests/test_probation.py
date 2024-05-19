import os

import pytest
from gypsum_client import (
    approve_probation,
    complete_upload,
    fetch_summary,
    reject_probation,
    remove_asset,
    start_upload,
)

__author__ = "Jayaram Kancherla"
__copyright__ = "Jayaram Kancherla"
__license__ = "MIT"

app_url = "https://gypsum-test.artifactdb.com"


@pytest.mark.skipif(
    "gh_token" not in os.environ, reason="GitHub token not in environment"
)
def test_probation_approve():
    gh_token = os.environ.get("gh_token", None)
    if gh_token is None:
        raise ValueError("GitHub token not in environment")

    remove_asset("test-Py", "probation", url=app_url, token=gh_token)

    init = start_upload(
        project="test-Py",
        asset="probation",
        version="v1",
        files=[],
        probation=True,
        token=gh_token,
        url=app_url,
    )

    complete_upload(init, url=app_url)

    _summary = fetch_summary("test-Py", "probation", "v1", cache_dir=None, url=app_url)
    assert _summary["on_probation"] is True

    approve_probation("test-Py", "probation", "v1", token=gh_token, url=app_url)
    _summary_after = fetch_summary(
        "test-Py", "probation", "v1", cache_dir=None, url=app_url
    )
    assert "on_probation" not in _summary_after


@pytest.mark.skipif(
    "gh_token" not in os.environ, reason="GitHub token not in environment"
)
def test_probation_reject():
    gh_token = os.environ.get("gh_token", None)
    if gh_token is None:
        raise ValueError("GitHub token not in environment")

    remove_asset("test-Py", "probation", url=app_url, token=gh_token)

    init = start_upload(
        project="test-Py",
        asset="probation",
        version="v1",
        files=[],
        probation=True,
        token=gh_token,
        url=app_url,
    )

    complete_upload(init, url=app_url)

    _summary = fetch_summary("test-Py", "probation", "v1", cache_dir=None, url=app_url)
    assert _summary["on_probation"] is True

    reject_probation("test-Py", "probation", "v1", token=gh_token, url=app_url)

    with pytest.raises(Exception):
        fetch_summary("test-Py", "probation", "v1", cache_dir=None, url=app_url)
