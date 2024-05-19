import hashlib
import os
import shutil
import tempfile
from pathlib import Path

import pytest
from gypsum_client import (
    abort_upload,
    complete_upload,
    fetch_manifest,
    list_assets,
    remove_asset,
    start_upload,
    upload_directory,
    upload_files,
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


@pytest.mark.skipif(
    "gh_token" not in os.environ, reason="GitHub token not in environment"
)
def test_upload_sequence_links():
    gh_token = os.environ.get("gh_token", None)
    if gh_token is None:
        raise ValueError("GitHub token not in environment")

    remove_asset("test-Py", asset="upload", token=gh_token, url=app_url)

    tmp = tempfile.mkdtemp()
    try:
        fpath = os.path.join(tmp, "test.json")
        with open(fpath, "w") as f:
            f.write('[ "Aaron" ]')

        link_df = [
            {
                "from.path": "whee/stuff.txt",
                "to.project": "test-R",
                "to.asset": "basic",
                "to.version": "v1",
                "to.path": "blah.txt",
            },
            {
                "from.path": "michaela",
                "to.project": "test-R",
                "to.asset": "basic",
                "to.version": "v1",
                "to.path": "foo/bar.txt",
            },
        ]

        init = start_upload(
            project="test-Py",
            asset="upload",
            version="1",
            files=[
                {
                    "path": "test.json",
                    "size": os.path.getsize(fpath),
                    "md5sum": hashlib.md5(open(fpath, "rb").read()).hexdigest(),
                }
            ],
            links=link_df,
            directory=tmp,
            token=gh_token,
            url=app_url,
        )

        assert len(init["file_urls"]) == 1
        upload_files(init, directory=tmp, url=app_url)
        complete_upload(init, url=app_url)

        man = fetch_manifest("test-Py", "upload", "1", cache_dir=None, url=app_url)

        assert sorted(man.keys()) == ["michaela", "test.json", "whee/stuff.txt"]
        assert man["michaela"]["link"] is not None
        assert man["whee/stuff.txt"]["link"] is not None
        assert "link" not in man["test.json"]
    finally:
        shutil.rmtree(tmp)


@pytest.mark.skipif(
    "gh_token" not in os.environ, reason="GitHub token not in environment"
)
def test_aborting_upload():
    gh_token = os.environ.get("gh_token", None)
    if gh_token is None:
        raise ValueError("GitHub token not in environment")

    remove_asset("test-Py", asset="upload", token=gh_token, url=app_url)

    init = start_upload(
        project="test-Py",
        asset="upload",
        version="1",
        files=[],
        token=gh_token,
        url=app_url,
    )

    assert len(init["file_urls"]) == 0
    assert "upload" in list_assets("test-Py", url=app_url)

    abort_upload(init, url=app_url)
    assert "upload" not in list_assets("test-Py", url=app_url)


@pytest.mark.skipif(
    "gh_token" not in os.environ, reason="GitHub token not in environment"
)
def test_upload_directory():
    gh_token = os.environ.get("gh_token", None)
    if gh_token is None:
        raise ValueError("GitHub token not in environment")

    remove_asset("test-Py", asset="upload-dir", token=gh_token, url=app_url)

    tmp = tempfile.mkdtemp()
    try:
        with open(os.path.join(tmp, "blah.txt"), "w") as f:
            f.write("ABCDEFGHIJKLMNOPQRSTUVWXYZ")

        os.makedirs(os.path.join(tmp, "foo"))
        with open(os.path.join(tmp, "foo", "bar.txt"), "w") as f:
            f.write("\n".join(map(str, range(1, 11))))

        upload_directory(
            tmp, "test-Py", "upload-dir", version="1", token=gh_token, url=app_url
        )

        man = fetch_manifest("test-Py", "upload-dir", "1", cache_dir=None, url=app_url)
        assert sorted(man.keys()) == ["blah.txt", "foo/bar.txt"]
        assert all("link" not in x for x in man.values())
    finally:
        shutil.rmtree(tmp)
