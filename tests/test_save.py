import os
import tempfile

import pytest
from gypsum_client import save_file, save_version

__author__ = "Jayaram Kancherla"
__copyright__ = "Jayaram Kancherla"
__license__ = "MIT"

blah_contents = (
    "A\nB\nC\nD\nE\nF\nG\nH\nI\nJ\nK\nL\nM\nN\nO\nP\nQ\nR\nS\nT\nU\nV\nW\nX\nY\nZ\n"
)
foobar_contents = "1 2 3 4 5\n6 7 8 9 10\n"


def test_save_file_works_as_expected():
    cache = tempfile.mkdtemp()

    out = save_file("test-R", "basic", "v1", "blah.txt", cache_dir=cache)
    assert open(out, "r").read() == blah_contents

    out = save_file("test-R", "basic", "v1", "foo/bar.txt", cache_dir=cache)
    assert open(out, "r").read() == foobar_contents

    # Actually uses the cache.
    with open(out, "w") as f:
        f.write("".join(list(map(chr, range(97, 123)))))
    out = save_file("test-R", "basic", "v1", "foo/bar.txt", cache_dir=cache)
    assert open(out, "r").read() == "".join(list(map(chr, range(97, 123))))

    # Until it doesn't.
    out = save_file(
        "test-R", "basic", "v1", "foo/bar.txt", cache_dir=cache, overwrite=True
    )
    assert open(out, "r").read() == foobar_contents

    with pytest.raises(Exception):
        save_file("test-R", "basic", "v1", "no.exist.txt", cache_dir=cache)


def test_save_file_works_via_links():
    cache = tempfile.mkdtemp()
    out = save_file("test-R", "basic", "v2", "blah.txt", cache_dir=cache)
    assert open(out, "r").read() == blah_contents

    out = save_file("test-R", "basic", "v2", "foo/bar.txt", cache_dir=cache)
    assert open(out, "r").read() == foobar_contents

    # Pulling out some ancestors.
    out = save_file("test-R", "basic", "v3", "blah.txt", cache_dir=cache)
    assert open(out, "r").read() == blah_contents

    out = save_file("test-R", "basic", "v3", "foo/bar.txt", cache_dir=cache)
    assert open(out, "r").read() == foobar_contents


def test_save_version_works_as_expected_without_links():
    cache = tempfile.mkdtemp()

    out = save_version("test-R", "basic", "v1", cache_dir=cache)
    assert os.path.exists(os.path.join(out, "..manifest"))
    assert open(os.path.join(out, "blah.txt"), "r").read() == blah_contents
    assert open(os.path.join(out, "foo", "bar.txt"), "r").read() == foobar_contents

    # Caching behaves as expected.
    path = os.path.join(out, "blah.txt")
    with open(path, "w") as f:
        f.write("foo")
    out = save_version("test-R", "basic", "v1", cache_dir=cache)
    assert open(path, "r").read() == "foo"

    # Unless we overwrite.
    out = save_version("test-R", "basic", "v1", cache_dir=cache, overwrite=True)
    assert open(path, "r").read() == blah_contents

    # Also works concurrently.
    cache2 = tempfile.mkdtemp()

    out = save_version("test-R", "basic", "v1", cache_dir=cache2, concurrent=2)
    assert os.path.exists(
        os.path.join(cache2, "bucket", "test-R", "basic", "v1", "..manifest")
    )
    assert (
        open(
            os.path.join(cache2, "bucket", "test-R", "basic", "v1", "blah.txt"), "r"
        ).read()
        == blah_contents
    )
    assert (
        open(
            os.path.join(cache2, "bucket", "test-R", "basic", "v1", "foo", "bar.txt"),
            "r",
        ).read()
        == foobar_contents
    )


def test_save_version_works_as_expected_with_links():
    cache = tempfile.mkdtemp()

    out = save_version("test-R", "basic", "v2", cache_dir=cache)
    assert open(os.path.join(out, "blah.txt"), "r").read() == blah_contents
    assert open(os.path.join(out, "foo", "bar.txt"), "r").read() == foobar_contents
    assert os.path.exists(
        os.path.join(cache, "bucket", "test-R", "basic", "v1", "blah.txt")
    )  # populates the linked-to files as well.
    assert os.path.exists(
        os.path.join(cache, "bucket", "test-R", "basic", "v1", "foo", "bar.txt")
    )

    # Unless we turn off link resolution.
    cache = tempfile.mkdtemp()

    out = save_version("test-R", "basic", "v2", cache_dir=cache, relink=False)
    assert not os.path.exists(os.path.join(out, "blah.txt"))
    assert not os.path.exists(os.path.join(out, "foo", "bar.txt"))

    # Works recursively.
    cache = tempfile.mkdtemp()

    out = save_version("test-R", "basic", "v3", cache_dir=cache)
    assert open(os.path.join(out, "blah.txt"), "r").read() == blah_contents
    assert open(os.path.join(out, "foo", "bar.txt"), "r").read() == foobar_contents
    assert os.path.exists(
        os.path.join(cache, "bucket", "test-R", "basic", "v1", "blah.txt")
    )  # populates the ancestral versions as well.
    assert os.path.exists(
        os.path.join(cache, "bucket", "test-R", "basic", "v1", "foo", "bar.txt")
    )

    # Link resolver doesn't do more work if it's already present.
    path = os.path.join(out, "foo", "bar.txt")
    with open(path, "w") as f:
        f.write("Aaron wuz here")
    out = save_version("test-R", "basic", "v3", cache_dir=cache)
    assert open(path, "r").read() == "Aaron wuz here"

    # Unless we force it to.
    out = save_version("test-R", "basic", "v3", cache_dir=cache, overwrite=True)
    assert open(path, "r").read() == foobar_contents
