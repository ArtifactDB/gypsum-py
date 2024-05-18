import os
import tempfile
import time
import warnings

import requests
from filelock import FileLock

from ._utils import _cache_directory, _download_and_rename_file
from .config import REQUESTS_MOD

__author__ = "Jayaram Kancherla"
__copyright__ = "Jayaram Kancherla"
__license__ = "MIT"

LAST_CHECK = {"req_time": None, "mod_time": None}


def fetch_metadata_database(
    name: str = "bioconductor.sqlite3", cache_dir: str = None, overwrite: bool = False
) -> str:
    """Fetch the SQLite database containing metadata from the gypsum backend.

    This function will automatically check for updates to the SQLite files
    and will download new versions accordingly. New checks are performed when one hour
    or more has elapsed since the last check. If the check fails, a warning is raised
    and the function returns the currently cached file.

    Args:
        name:
            Name of the database.
            This can be the name of any SQLite file in
            https://github.com/ArtifactDB/bioconductor-metadata-index/releases/tag/latest.

            Defaults to "bioconductor.sqlite3".

        cache_dir:
            Path to the cache directory.

            Defaults to None.

        overwrite:
            Whether to overwrite existing file.

            Defaults to False.

    Returns:
        Path to the downloaded database.
    """
    base_url = "https://github.com/ArtifactDB/bioconductor-metadata-index/releases/download/latest/"

    if cache_dir is None:
        cache_path = tempfile.NamedTemporaryFile(suffix=".sqlite3").name
    else:
        cache_dir = os.path.join(_cache_directory(cache_dir), "databases")

        cache_path = os.path.join(cache_dir, name)
        if not os.path.exists(cache_path):
            os.makedirs(os.path.dirname(cache_path), exist_ok=True)

        if os.path.exists(cache_path) and not overwrite:
            old_lastmod_raw = None

            _lock = FileLock(cache_path + ".lock")
            if not _lock.is_locked:
                old_lastmod_raw = open(cache_path + ".modified").readlines()

            old_lastmod = float(old_lastmod_raw[0])
            new_lastmod = get_last_modified_date(base_url)

            if new_lastmod is not None and old_lastmod == new_lastmod:
                return cache_path

    _lock = FileLock(cache_path + ".lock")
    with _lock:
        mod_path = cache_path + ".modified"
        _download_and_rename_file(base_url + "modified", mod_path)
        _download_and_rename_file(base_url + name, cache_path)

    LAST_CHECK["req_time"] = get_current_unix_time()
    LAST_CHECK["mod_time"] = float(open(mod_path).readline())

    return cache_path


def get_current_unix_time():
    return time.time() * 1000  # milliseconds


def get_last_modified_date(base_url):
    curtime = get_current_unix_time()
    if (
        LAST_CHECK["req_time"] is not None
        and LAST_CHECK["req_time"] + 60 * 60 * 1000 >= curtime
    ):
        return LAST_CHECK["mod_time"]

    mod_time = None
    try:
        url = base_url + "modified"
        response = requests.get(url, verify=REQUESTS_MOD["verify"])
        mod_time = float(response.text)
    except Exception as e:
        warnings.warn(
            f"Failed to check the last modified timestamp: {str(e)}", UserWarning
        )

    if mod_time is not None:
        LAST_CHECK["req_time"] = curtime
        LAST_CHECK["mod_time"] = mod_time

    return mod_time
