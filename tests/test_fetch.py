import json
import os
import tempfile
from datetime import datetime

import pytest
from gypsum_client.fetch_operations import (
    fetch_latest,
    fetch_manifest,
    fetch_permissions,
    fetch_quota,
    fetch_summary,
    fetch_usage,
)
from gypsum_client.fetch_metadata_schema import fetch_metadata_schema

__author__ = "Jayaram Kancherla"
__copyright__ = "Jayaram Kancherla"
__license__ = "MIT"


def test_fetch_manifest():
    cache = tempfile.mkdtemp()
    man = fetch_manifest("test-R", "basic", "v1", cache_dir=cache)
    assert sorted(man.keys()) == ["blah.txt", "foo/bar.txt"]

    # Uses the cache.
    with open(
        os.path.join(cache, "bucket", "test-R", "basic", "v1", "..manifest"), "w"
    ) as f:
        f.write("[]")

    man = fetch_manifest("test-R", "basic", "v1", cache_dir=cache)
    assert len(man) == 0

    # Unless we overwrite it.
    man = fetch_manifest("test-R", "basic", "v1", cache_dir=cache, overwrite=True)
    assert len(man) > 0

    with pytest.raises(Exception):
        fetch_manifest("test-R", "basic", "non-existent", cache_dir=cache)


def test_fetch_summary():
    cache = tempfile.mkdtemp()
    xx = fetch_summary("test-R", "basic", "v1", cache_dir=cache)
    original_user = xx["upload_user_id"]
    assert isinstance(xx["upload_start"], datetime)
    assert isinstance(xx["upload_finish"], datetime)

    # Uses the cache.
    sumpath = os.path.join(cache, "bucket", "test-R", "basic", "v1", "..summary")
    with open(sumpath, "w") as f:
        json.dump(
            {
                "upload_user_id": "adrian",
                "upload_start": "2022-01-01T01:01:01Z",
                "upload_finish": "2022-01-01T01:01:02Z",
            },
            f,
        )
    xx = fetch_summary("test-R", "basic", "v1", cache_dir=cache)
    assert xx["upload_user_id"] == "adrian"

    # Unless we overwrite it.
    xx = fetch_summary("test-R", "basic", "v1", cache_dir=cache, overwrite=True)
    assert xx["upload_user_id"] == original_user

    # Self-deletes from the cache if it's on probation.
    with open(sumpath, "w") as f:
        json.dump(
            {
                "upload_user_id": "adrian",
                "upload_start": "2022-01-01T01:01:01Z",
                "upload_finish": "2022-01-01T01:01:02Z",
                "on_probation": True,
            },
            f,
        )
    xx = fetch_summary("test-R", "basic", "v1", cache_dir=cache)
    assert xx["on_probation"]
    assert not os.path.exists(sumpath)

    with pytest.raises(Exception):
        fetch_summary("test-R", "basic", "non-existent", cache_dir=cache)


def test_fetch_latest():
    assert fetch_latest("test-R", "basic") == "v3"


def test_fetch_usage():
    assert fetch_usage("test-R") > 0


def test_fetch_permissions():
    perms = fetch_permissions("test-R")
    assert isinstance(perms["owners"], list)
    assert isinstance(perms["uploaders"], list)
