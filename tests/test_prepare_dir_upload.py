import os
import shutil
import tempfile

import pytest
from gypsum_client import clone_version, prepare_directory_upload

__author__ = "Jayaram Kancherla"
__copyright__ = "Jayaram Kancherla"
__license__ = "MIT"


def test_prepare_directory_upload_works_as_expected():
    cache = tempfile.mkdtemp()
    dest = tempfile.mkdtemp()
    clone_version("test-R", "basic", "v1", destination=dest, cache_dir=cache)
    with open(os.path.join(dest, "heanna"), "w") as f:
        f.write("sumire")

    prepped = prepare_directory_upload(dest, cache_dir=cache)
    if os.name == "nt":  # Windows
        assert prepped["files"] == ["blah.txt", "foo/bar.txt", "heanna"]
        assert len(prepped["links"]) == 0
    else:  # Unix
        assert prepped["files"] == ["heanna"]
        assert sorted(x["from.path"] for x in prepped["links"]) == sorted(
            ["blah.txt", "foo/bar.txt"]
        )
        assert sorted(x["to.project"] for x in prepped["links"]) == sorted(
            ["test-R", "test-R"]
        )
        assert sorted(x["to.asset"] for x in prepped["links"]) == sorted(
            ["basic", "basic"]
        )
        assert sorted(x["to.version"] for x in prepped["links"]) == sorted(["v1", "v1"])
        assert sorted(x["to.path"] for x in prepped["links"]) == sorted(
            ["blah.txt", "foo/bar.txt"]
        )

    prepped = prepare_directory_upload(dest, cache_dir=cache, links="never")
    assert sorted(prepped["files"]) == sorted(["blah.txt", "foo/bar.txt", "heanna"])
    assert len(prepped["links"]) == 0

    shutil.rmtree(cache)
    shutil.rmtree(dest)


@pytest.mark.skipif(os.name == "nt", reason="skipping symlink tests on Windows")
def test_prepare_directory_upload_with_some_odd_things():
    cache = tempfile.mkdtemp()
    dest = tempfile.mkdtemp()
    clone_version("test-R", "basic", "v1", destination=dest, cache_dir=cache)

    with open(os.path.join(dest, "..check"), "w") as f:
        f.write("stuff")

    random = tempfile.mktemp()
    os.symlink(random, os.path.join(dest, "arkansas"))

    with pytest.raises(Exception):
        prepare_directory_upload(dest, cache_dir=cache, links="always")

    with pytest.raises(Exception):
        prepare_directory_upload(dest, cache_dir=cache, links="never")

    with pytest.raises(Exception):
        prepare_directory_upload(dest, cache_dir=cache)

    with open(random, "w") as f:
        f.write("YAY")

    prepped = prepare_directory_upload(dest, cache_dir=cache)
    assert sorted(prepped["files"]) == sorted(["..check", "arkansas"])
    assert sorted(x["from.path"] for x in prepped["links"]) == sorted(
        ["blah.txt", "foo/bar.txt"]
    )

    shutil.rmtree(cache)
    shutil.rmtree(dest)


@pytest.mark.skipif(os.name == "nt", reason="skipping symlink tests on Windows")
def test_prepare_directory_upload_handles_dangling_links_correctly():
    cache = tempfile.mkdtemp()
    dest = tempfile.mkdtemp()
    clone_version(
        "test-R", "basic", "v1", destination=dest, cache_dir=cache, download=False
    )

    prepped = prepare_directory_upload(dest, cache_dir=cache)
    assert prepped["files"] == []
    assert len(prepped["links"]) == 2

    with pytest.raises(Exception):
        prepare_directory_upload(dest, cache_dir=cache, links="never")

    shutil.rmtree(cache)
    shutil.rmtree(dest)
