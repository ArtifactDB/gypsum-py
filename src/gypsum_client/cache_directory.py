import os
from pathlib import Path
from typing import Optional

__author__ = "Jayaram Kancherla"
__copyright__ = "Jayaram Kancherla"
__license__ = "MIT"

CURRENT_CACHE_DIRECTORY = None


def cache_directory(dir: Optional[str] = None) -> str:
    """Cache directory.

    Specify the cache directory in the local filesystem
    for gypsum-related data.

    If the ``GYPSUM_CACHE_DIR`` environment variable is set
    before the first call to ``cache_directory()``, it is used
    as the initial location of the cache directory.
    Otherwise, the initial location is set to user's home
    directory defined by ``appdirs.user_cache_dir()``.

    Args:
        dir:
            Path to the current cache directory.  If `None`, a default cache
            location is chosen.

    Returns:
        If ``dir`` is ``None``, the path to the cache directory is returned.

        If ``dir`` is supplied, it is used to set the path to the cache
        directory, and the previous location of the directory is returned.
    """
    global CURRENT_CACHE_DIRECTORY

    if CURRENT_CACHE_DIRECTORY is None:
        _from_env = os.environ.get("GYPSUM_CACHE_DIR", None)
        if _from_env is not None:
            CURRENT_CACHE_DIRECTORY = _from_env
        else:
            import appdirs
            CURRENT_CACHE_DIRECTORY = appdirs.user_cache_dir("gypsum", "ArtifactDB")

    prev = CURRENT_CACHE_DIRECTORY
    if dir is not None:
        CURRENT_CACHE_DIRECTORY = dir
    return prev
