import os
import tempfile

import requests
from filelock import FileLock

from ._utils import _cache_directory

__author__ = "Jayaram Kancherla"
__copyright__ = "Jayaram Kancherla"
__license__ = "MIT"


def fetch_metadata_schema(
    name: str = "bioconductor/v1.json",
    cache_dir: str = None,
    overwrite: bool = False,
) -> str:
    """Fetch a JSON schema file for metadata to be inserted into a SQLite database.

    Args:
        name:
            Name of the schema.
            Defaults to "bioconductor/v1.json".

        cache_dir:
            Path to the cache directory.

        overwrite:
            Whether to overwrite existing file in cache.

    Returns:
        Path containing the downloaded schema.
    """
    cache_path = None
    if cache_dir is None:
        cache_path = tempfile.mktemp(suffix=".json")
    else:
        cache_dir = os.path.join(_cache_directory(cache_dir), "schemas")

        cache_path = os.path.join(cache_dir, name)
        if not os.path.exists(cache_path):
            os.makedirs(os.path.dirname(cache_path), exist_ok=True)

        if os.path.exists(cache_path) and not overwrite:
            _lock = FileLock(cache_path)
            if not _lock.is_locked:
                return cache_path

    _lock = FileLock(cache_path)
    with _lock:
        url = "https://artifactdb.github.io/bioconductor-metadata-index/" + name
        response = requests.get(url)
        with open(cache_path, "wb") as f:
            f.write(response.content)

    return cache_path
