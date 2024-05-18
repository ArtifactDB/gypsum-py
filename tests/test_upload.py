import os
import tempfile
from pathlib import Path

import pytest
from gypsum_client.complete_upload import complete_upload
from gypsum_client.fetch_assets import fetch_manifest
from gypsum_client.remove_assets import remove_asset
from gypsum_client.start_upload import start_upload
from gypsum_client.upload_assets import upload_files

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
def test_upload_regular():
    gh_token = os.environ.get("gh_token", None)
    if gh_token is None:
        raise ValueError("GitHub token not in environment")

    remove_asset("test-Py", asset="upload", token=gh_token, url=app_url)
    tmp_dir = tempfile.mkdtemp()

    with open(f"{tmp_dir}/blah.txt", "w") as f:
        f.write(blah_contents)

    os.makedirs(f"{tmp_dir}/foo", exist_ok=True)

    with open(f"{tmp_dir}/foo/blah.txt", "w") as f:
        f.write(foobar_contents)

    files = [
        str(file.relative_to(tmp_dir))
        for file in Path(tmp_dir).rglob("*")
        if not os.path.isdir(file)
    ]

    init = start_upload(
        project="test-Py",
        asset="upload",
        version="1",
        files=files,
        directory=tmp_dir,
        token=gh_token,
        url=app_url,
    )

    assert len(init["file_urls"]) == 2
    assert isinstance(init["abort_url"], str)
    assert isinstance(init["complete_url"], str)
    assert isinstance(init["session_token"], str)

    upload_files(init, directory=tmp_dir, url=app_url)
    complete_upload(init, url=app_url)

    man = fetch_manifest("test-Py", "upload", "1", cache_dir=None, url=app_url)
    assert sorted(man.keys()) == ["blah.txt", "foo/blah.txt"]
    assert all(man[file].get("link") is None for file in man.keys())
