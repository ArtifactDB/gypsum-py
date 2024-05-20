import os
from pathlib import Path
from typing import Optional

__author__ = "Jayaram Kancherla"
__copyright__ = "Jayaram Kancherla"
__license__ = "MIT"

CURRENT_CACHE_DIRECTORY = None


def cache_directory(dir: Optional[str] = None):
    """Cache directory.

    Specify the cache directory in the local filesystem
    for gypsum-related data.

    If the ``GYPSUM_CACHE_DIR`` environment variable is set
    before the first call to ``cache_directory()``, it is used
    as the initial location of the cache directory.
    Otherwise, the initial location is set to user's home
    directory defined by ``Path.home()``.

    Args:
        dir:
            Path to the cache directory.
            If `None`, a default cache location is used.

    Returns:
        Path to the cache directory.
    """
    global CURRENT_CACHE_DIRECTORY

    if CURRENT_CACHE_DIRECTORY is None:
        _from_env = os.environ.get("GYPSUM_CACHE_DIR", None)
        if _from_env is not None:
            if not os.path.exists(_from_env):
                raise FileNotFoundError(
                    f"Path {_from_env} does not exist or is not accessible."
                )

            CURRENT_CACHE_DIRECTORY = _from_env
        else:
            CURRENT_CACHE_DIRECTORY = os.path.join(str(Path.home()), "gypsum", "cache")
            os.makedirs(CURRENT_CACHE_DIRECTORY, exist_ok=True)

    if dir is not None:
        if not os.path.exists(dir):
            raise FileNotFoundError(f"Path {dir} does not exist or is not accessible.")
        CURRENT_CACHE_DIRECTORY = dir

    return CURRENT_CACHE_DIRECTORY
