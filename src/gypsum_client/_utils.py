import os
from pathlib import Path
from typing import Optional
from urllib.parse import quote

import requests

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


def _list_for_prefix(
    prefix: str,
    url: str,
    recursive: bool = False,
    include_dot: bool = False,
    only_dirs: bool = True,
):
    url = url + "/list"

    qparams = {"recursive": "true" if recursive is True else "false"}
    if prefix is not None:
        qparams["prefix"] = prefix

    req = requests.get(url, params=qparams)
    req.raise_for_status()

    resp = req.json()
    if only_dirs is True:
        resp = [val for val in resp if val.endswith("/")]

    if prefix is not None:
        resp = [val.replace(prefix, "") for val in resp if val.startswith(prefix)]

    if include_dot is False:
        resp = [_remove_slash_url(val) for val in resp if not val.startswith("..")]

    return resp


def _fetch_json(path: str, url: str):
    full_url = f"{url}/file/{quote(path)}"

    req = requests.get(full_url)
    req.raise_for_status()

    return req.json()
