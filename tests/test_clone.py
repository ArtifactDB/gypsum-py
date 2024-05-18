import os
import tempfile

import pytest
from gypsum_client import clone_version

__author__ = "Jayaram Kancherla"
__copyright__ = "Jayaram Kancherla"
__license__ = "MIT"


def test_clone_version_works_as_expected_with_existing_files():
    cache = tempfile.mkdtemp()
    dest = tempfile.mkdtemp()
    clone_version("test-R", "basic", "v1", destination=dest, cache_dir=cache)

    d1 = os.path.join(dest, "blah.txt")
    if os.name != "nt":  # os.name != 'nt' for non-Windows platforms
        l1 = os.readlink(d1)
        assert os.path.exists(l1)
        assert l1.endswith("test-R/basic/v1/blah.txt")
    else:
        assert os.path.exists(d1)

    d2 = os.path.join(dest, "foo/bar.txt")
    if os.name != "nt":
        l2 = os.readlink(d2)
        assert os.path.exists(l2)
        assert l2.endswith("test-R/basic/v1/foo/bar.txt")
    else:
        assert os.path.exists(d2)


@pytest.mark.skipif(
    os.name == "nt",
    reason="download=False can't work on Windows if symbolic links aren't available.",
)
def test_clone_version_happily_works_without_any_download():
    cache = tempfile.mkdtemp()
    dest = tempfile.mkdtemp()
    clone_version(
        "test-R", "basic", "v1", download=False, destination=dest, cache_dir=cache
    )

    l1 = os.readlink(os.path.join(dest, "blah.txt"))
    assert l1.endswith("test-R/basic/v1/blah.txt")
    assert not os.path.exists(l1)

    l2 = os.readlink(os.path.join(dest, "foo/bar.txt"))
    assert l2.endswith("test-R/basic/v1/foo/bar.txt")
    assert not os.path.exists(l2)


@pytest.mark.skipif(
    os.name == "nt",
    reason="download=False can't work on Windows if symbolic links aren't available.",
)
def test_clone_version_works_correctly_if_version_itself_contains_links():
    cache = tempfile.mkdtemp()
    dest = tempfile.mkdtemp()
    clone_version(
        "test-R",
        "basic",
        "v2",
        destination=dest,
        cache_dir=cache,
        download=False,
        relink=False,
    )

    l1 = os.readlink(os.path.join(dest, "blah.txt"))
    assert l1.endswith("test-R/basic/v2/blah.txt")
    assert not os.path.exists(l1)

    l2 = os.readlink(os.path.join(dest, "foo/bar.txt"))
    assert l2.endswith("test-R/basic/v2/foo/bar.txt")
    assert not os.path.exists(l2)
