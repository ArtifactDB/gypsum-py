import os
import tempfile

import pytest
from gypsum_client.fetch_metadata_database import fetch_metadata_database, LAST_CHECK


__author__ = "Jayaram Kancherla"
__copyright__ = "Jayaram Kancherla"
__license__ = "MIT"


def test_fetch_metadata_database():
    _cache_dir = tempfile.mkdtemp()

    path = fetch_metadata_database(cache_dir=_cache_dir)
    assert os.path.getsize(path) > 0
    assert isinstance(LAST_CHECK["req_time"], float)
    assert not isinstance(LAST_CHECK["req_time"], bool)
    assert not isinstance(LAST_CHECK["mod_time"], bool)
    assert isinstance(LAST_CHECK["mod_time"], float)

    # Uses the cache.
    with open(path, "w") as f:
        f.write("FOO_BAR")

    path2 = fetch_metadata_database(cache_dir=_cache_dir)
    assert path == path2

    assert open(path).read().strip() == "FOO_BAR"
