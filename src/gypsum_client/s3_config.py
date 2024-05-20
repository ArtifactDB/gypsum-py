import json
import os
import time
from typing import Optional

import requests
from filelock import FileLock

from .cache_directory import cache_directory
from .config import REQUESTS_MOD
from .rest_url import rest_url

__author__ = "Jayaram Kancherla"
__copyright__ = "Jayaram Kancherla"
__license__ = "MIT"


CREDS_CACHE = {"uncached": None, "info": {}}


def _config_cache_path(cache_dir):
    return os.path.join(cache_dir, "credentials", "s3.json")


def public_s3_config(
    refresh: bool = False, url: str = rest_url(), cache_dir: Optional[str] = None
) -> dict:
    """Get S3 configuration to the bucket storing the data.

    Users can use this downstream to access the bucket directly using boto3.

    Args:
        refresh:
            Whether to refresh the cached credentials.
            Defaults to False.

        url:
            URL to the gypsum compatible API.

        cache_dir:
            Path to the cache directory.
            Defaults to None.

    Returns:
        A dictionary containing the S3 credentials.
    """
    creds = None

    if not refresh:
        if cache_dir is None:
            creds = CREDS_CACHE["uncached"]
            if creds is not None:
                return creds
        else:
            creds = CREDS_CACHE["info"].get(cache_dir)
            if creds is not None:
                return creds

            cache_path = _config_cache_path(cache_dir)
            if os.path.exists(cache_path):
                _lock = FileLock(cache_path + ".LOCK")
                with _lock:
                    with open(cache_dir, "r") as f:
                        creds = json.load(f)

                if (time.time() - os.path.getctime(cache_dir)) <= (
                    1 * 7 * 24 * 60 * 60
                ):
                    CREDS_CACHE["info"][cache_dir] = creds
                    return creds

    req = requests.get(url + "/credentials/s3-api", verify=REQUESTS_MOD["verify"])
    creds = req.json()

    if cache_dir is None:
        CREDS_CACHE["uncached"] = creds
    else:
        CREDS_CACHE["info"][cache_dir] = creds
        config_path = _config_cache_path(cache_dir)
        os.makedirs(os.path.dirname(config_path), exist_ok=True)

        with FileLock(config_path + ".LOCK"):
            with open(config_path, "w") as f:
                json.dump(creds, f)

    return creds
