from gypsum_client.list_operations import (
    list_assets,
    list_files,
    list_projects,
    list_versions,
)

__author__ = "Jayaram Kancherla"
__copyright__ = "Jayaram Kancherla"
__license__ = "MIT"


def test_list_projects():
    projects = list_projects()
    assert "test-R" in projects


def test_list_assets():
    assets = list_assets("test-R")
    assert "basic" in assets


def test_list_versions():
    versions = list_versions("test-R", "basic")
    assert "v1" in versions
    assert "v2" in versions
    assert "v3" in versions


def test_list_files():
    in_basic = list_files("test-R", "basic", "v1")
    assert sorted(in_basic) == sorted(
        ["..summary", "..manifest", "blah.txt", "foo/bar.txt"]
    )

    in_basic = list_files("test-R", "basic", "v2")
    assert sorted(in_basic) == sorted(
        ["..summary", "..manifest", "..links", "foo/..links"]
    )

    in_basic = list_files("test-R", "basic", "v1", prefix="foo/")
    assert sorted(in_basic) == sorted(["foo/bar.txt"])

    in_basic = list_files("test-R", "basic", "v1", prefix="..")
    assert sorted(in_basic) == sorted(["..summary", "..manifest"])
