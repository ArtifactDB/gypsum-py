import os

import pytest
from gypsum_client.complete_upload import complete_upload
from gypsum_client.create_assets import create_project
from gypsum_client.fetch_assets import fetch_latest, fetch_manifest, fetch_usage
from gypsum_client.remove_assets import remove_asset, remove_project, remove_version
from gypsum_client.start_upload import start_upload

__author__ = "Jayaram Kancherla"
__copyright__ = "Jayaram Kancherla"
__license__ = "MIT"


@pytest.mark.skipif(
    "gh_token" not in os.environ, reason="GitHub token not in environment"
)
def test_remove_functions():
    gh_token = os.environ.get("gh_token", None)
    if gh_token is None:
        raise ValueError("GitHub token not in environment")

    remove_project("test-R-remove", token=gh_token)

    create_project("test-R-remove", owners="jkanche", token=gh_token)
    for v in ["v1", "v2"]:
        init = start_upload(
            project="test-R-remove",
            asset="sacrifice",
            version=v,
            files=[],
            token=gh_token,
        )
        complete_upload(init)

    fetch_manifest("test-R-remove", "sacrifice", "v2", cache_dir=None)
    remove_version("test-R-remove", "sacrifice", "v2", token=gh_token)
    with pytest.raises(Exception):
        fetch_manifest("test-R-remove", "sacrifice", "v2", cache_dir=None)

    assert fetch_latest("test-R-remove", "sacrifice") == "v1"
    remove_asset("test-R-remove", "sacrifice", token=gh_token)
    with pytest.raises(Exception):
        fetch_latest("test-R-remove", "sacrifice")

    fetch_usage("test-R-remove")
    remove_project("test-R-remove", token=gh_token)
    with pytest.raises(Exception):
        fetch_usage("test-R-remove")
