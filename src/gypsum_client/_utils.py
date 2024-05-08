import os
from pathlib import Path
from typing import Optional

__author__ = "Jayaram Kancherla"
__copyright__ = "Jayaram Kancherla"
__license__ = "MIT"


def _rest_url(url: Optional[str] = None):
    current = "https://gypsum.artifactdb.com"

    if url is None:
        return current
    else:
        return url


def _cache_directory(dir: Optional[str] = None):
    current = None
    if current is None:
        _from_env = os.environ.get("GYPSUM_CACHE_DIR", None)
        if _from_env is not None:
            if not os.path.exists(_from_env):
                raise FileNotFoundError(
                    f"Path {_from_env} does not exist or is not accessible."
                )

            current = _from_env
        else:
            current = os.path.join(str(Path.home()), "gypsum", "cache")

    if dir is None:
        return current
    else:
        if not os.path.exists(current):
            raise FileNotFoundError(
                f"Path {current} does not exist or is not accessible."
            )

        return current


def _remove_slash_url(url: str):
    if url.endswith("/"):
        url = url.rstrip("/")

    return url
