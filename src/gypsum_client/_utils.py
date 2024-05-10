import json
import os
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from urllib.parse import quote_plus

import requests
from filelock import FileLock

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
        if not os.path.exists(dir):
            raise FileNotFoundError(f"Path {dir} does not exist or is not accessible.")

        return dir


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
    full_url = f"{url}/file/{quote_plus(path)}"

    req = requests.get(full_url)
    req.raise_for_status()

    return req.json()


BUCKET_CACHE_NAME = "bucket"


def _fetch_cacheable_json(
    project: str,
    asset: str,
    version: str,
    path: str,
    cache: str,
    url: str,
    overwrite: bool,
):
    bucket_path = f"{project}/{asset}/{version}/{path}"

    if cache is None:
        return _fetch_json(bucket_path, url=url)
    else:
        _out_path = os.path.join(
            cache, BUCKET_CACHE_NAME, project, asset, version, path
        )

        _save_file(bucket_path, destination=_out_path, overwrite=overwrite, url=url)

        with open(_out_path, "r") as jf:
            return json.load(jf)


def _save_file(
    path: str, destination: str, overwrite: bool, url: str, error: bool = True
):
    if overwrite is True or not os.path.exists(destination):
        os.makedirs(os.path.dirname(destination), exist_ok=True)

        _lock = FileLock(destination)
        with _lock:
            with tempfile.NamedTemporaryFile(
                dir=os.path.dirname(destination), delete=False
            ) as tmp_file:
                try:
                    full_url = f"{url}/file/{quote_plus(path)}"

                    req = requests.get(full_url, stream=True)
                    req.raise_for_status()

                    for chunk in req.iter_content(chunk_size=None):
                        tmp_file.write(chunk)
                except Exception as e:
                    if error:
                        raise Exception(f"Failed to save '{path}'; {str(e)}.")
                    else:
                        return False

                # Rename the temporary file to the destination
                shutil.move(tmp_file.name, destination)

    return True


def _cast_datetime(x):
    if x.endswith("Z"):
        x = x[:-1]

    # Remove fractional seconds.
    x = x.split(".")[0]

    return datetime.strptime(x, "%Y-%m-%dT%H:%M:%S").astimezone(tz=timezone.utc)
