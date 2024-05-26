import os
import tempfile

import requests
from filelock import FileLock

from .cache_directory import cache_directory
from .config import REQUESTS_MOD

__author__ = "Jayaram Kancherla"
__copyright__ = "Jayaram Kancherla"
__license__ = "MIT"


def fetch_metadata_schema(
    name: str = "bioconductor/v1.json",
    cache_dir: str = cache_directory(),
    overwrite: bool = False,
) -> str:
    """Fetch a JSON schema file for metadata to be inserted into a SQLite database.

    Fetch a JSON schema file for metadata to be inserted into a SQLite database
    See `metadata index <https://github.com/ArtifactDB/bioconductor-metadata-index>`_
    for more details.

    Each SQLite database is created from metadata files uploaded to the gypsum backend,
    so clients uploading objects to be incorporated into the database should
    validate their metadata against the corresponding JSON schema.

    See Also:
        :py:func:`~gypsum_client.validate_metadata.validate_metadata`, to
        validate metadata against a chosen schema.

        :py:func:`~gypsum_client.fetch_metadata_database.fetch_metadata_database`,
        to obtain the SQLite database of metadata.

    Example:

        .. code-block:: python

            schema_path = fetch_metadata_schema()

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
        cache_dir = os.path.join(cache_dir, "schemas")

        cache_path = os.path.join(cache_dir, name)
        if not os.path.exists(cache_path):
            os.makedirs(os.path.dirname(cache_path), exist_ok=True)

        if os.path.exists(cache_path) and not overwrite:
            _lock = FileLock(cache_path + ".LOCK")
            if not _lock.is_locked:
                return cache_path

    _lock = FileLock(cache_path + ".LOCK")
    with _lock:
        url = "https://artifactdb.github.io/bioconductor-metadata-index/" + name
        response = requests.get(url, verify=REQUESTS_MOD["verify"])
        with open(cache_path, "wb") as f:
            f.write(response.content)

    return cache_path
