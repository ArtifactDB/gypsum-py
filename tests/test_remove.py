import os

import pytest
from gypsum_client import (
    complete_upload,
    create_project,
    fetch_latest,
    fetch_manifest,
    fetch_usage,
    remove_asset,
    remove_project,
    remove_version,
    start_upload,
)

__author__ = "Jayaram Kancherla"
__copyright__ = "Jayaram Kancherla"
__license__ = "MIT"

app_url = "https://gypsum-test.artifactdb.com"


@pytest.mark.skipif(
    "gh_token" not in os.environ, reason="GitHub token not in environment"
)
def test_remove_functions():
    gh_token = os.environ.get("gh_token", None)
    if gh_token is None:
        raise ValueError("GitHub token not in environment")

    remove_project("test-Py-remove", url=app_url, token=gh_token)

    create_project("test-Py-remove", owners=["jkanche"], url=app_url, token=gh_token)
    for v in ["v1", "v2"]:
        init = start_upload(
            project="test-Py-remove",
            asset="sacrifice",
            version=v,
            files=[],
            token=gh_token,
            url=app_url,
        )

        complete_upload(init, url=app_url)

    fetch_manifest("test-Py-remove", "sacrifice", "v2", url=app_url, cache_dir=None)
    remove_version("test-Py-remove", "sacrifice", "v2", url=app_url, token=gh_token)
    with pytest.raises(Exception):
        fetch_manifest("test-Py-remove", "sacrifice", "v2", url=app_url, cache_dir=None)

    assert fetch_latest("test-Py-remove", "sacrifice", url=app_url) == "v1"
    remove_asset("test-Py-remove", "sacrifice", url=app_url, token=gh_token)
    with pytest.raises(Exception):
        fetch_latest("test-Py-remove", "sacrifice", url=app_url)

    fetch_usage("test-Py-remove", url=app_url)
    remove_project("test-Py-remove", url=app_url, token=gh_token)
    with pytest.raises(Exception):
        fetch_usage("test-Py-remove", url=app_url)
