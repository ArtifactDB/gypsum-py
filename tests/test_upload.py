import os
import tempfile

import pytest
from gypsum_client.complete_upload import complete_upload
from gypsum_client.create_assets import create_project
from gypsum_client.fetch_assets import fetch_latest, fetch_manifest, fetch_usage
from gypsum_client.remove_assets import remove_asset, remove_project, remove_version
from gypsum_client.start_upload import start_upload

__author__ = "Jayaram Kancherla"
__copyright__ = "Jayaram Kancherla"
__license__ = "MIT"

blah_contents = (
    "A\nB\nC\nD\nE\nF\nG\nH\nI\nJ\nK\nL\nM\nN\nO\nP\nQ\nR\nS\nT\nU\nV\nW\nX\nY\nZ\n"
)
foobar_contents = "1 2 3 4 5\n6 7 8 9 10\n"


@pytest.mark.skipif(
    "gh_token" not in os.environ, reason="GitHub token not in environment"
)
def test_upload_regular():
    gh_token = os.environ.get("gh_token", None)
    if gh_token is None:
        raise ValueError("GitHub token not in environment")

    remove_asset("test-py", asset="upload", token=gh_token)
    tmp_dir = tempfile.mkdtemp()

    with open(f"{tmp_dir}/blah.txt") as f:
        f.write(blah_contents)
    os.makedirs(f"{tmp_dir}/foo", exist_ok=True)
    with open(f"{tmp_dir}/foo/blah.txt") as f:
        f.write_text(foobar_contents)

    init = start_upload(
        project="test-py",
        asset="upload",
        version="1",
        files=[str(file.relative_to(tmp_dir)) for file in tmp_dir.rglob("*")],
        directory=tmp_dir,
        token=gh_token,
    )

    assert len(init["file_urls"]) == 2
    assert isinstance(init["abort_url"], str)
    assert isinstance(init["complete_url"], str)
    assert isinstance(init["session_token"], str)

    upload_files(init, directory=tmp_dir)
    complete_upload(init)

    man = fetch_manifest("test-R", "upload", "1", cache=None)
    assert sorted(man.keys()) == ["blah.txt", "foo/bar.txt"]
    assert not any(man[file].get("link") is None for file in man)
