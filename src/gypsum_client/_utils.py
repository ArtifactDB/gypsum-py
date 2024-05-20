import json
import os
import re
import shutil
import tempfile
from datetime import datetime
from typing import Optional
from urllib.parse import quote_plus

import requests
from filelock import FileLock

from .config import REQUESTS_MOD

__author__ = "Jayaram Kancherla"
__copyright__ = "Jayaram Kancherla"
__license__ = "MIT"


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

    req = requests.get(url, params=qparams, verify=REQUESTS_MOD["verify"])
    try:
        req.raise_for_status()
    except Exception as e:
        raise Exception(
            f"Failed to access files from API, {req.status_code} and reason: {req.text}"
        ) from e

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

    req = requests.get(full_url, verify=REQUESTS_MOD["verify"])
    try:
        req.raise_for_status()
    except Exception as e:
        raise Exception(
            f"Failed to access json from API, {req.status_code} and reason: {req.text}"
        ) from e

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
    path: str,
    destination: str,
    overwrite: bool,
    url: str,
    error: bool = True,
    verify: Optional[bool] = None,
):
    if overwrite is True or not os.path.exists(destination):
        os.makedirs(os.path.dirname(destination), exist_ok=True)

        _lock = FileLock(destination + ".LOCK")
        with _lock:
            with tempfile.NamedTemporaryFile(
                dir=os.path.dirname(destination), delete=False
            ) as tmp_file:
                try:
                    full_url = f"{url}/file/{quote_plus(path)}"

                    if verify is None:
                        verify = REQUESTS_MOD["verify"]

                    req = requests.get(full_url, stream=True, verify=verify)
                    try:
                        req.raise_for_status()
                    except Exception as e:
                        raise Exception(
                            f"Failed to save file from API, {req.status_code} and reason: {req.text}"
                        ) from e

                    for chunk in req.iter_content(chunk_size=None):
                        tmp_file.write(chunk)
                except Exception as e:
                    if error:
                        raise Exception(f"Failed to save '{path}'; {str(e)}.") from e
                    else:
                        return False

                # Rename the temporary file to the destination
                shutil.move(tmp_file.name, destination)

    return True


def _cast_datetime(x):
    # Remove fractional seconds.
    if "." in x:
        x = x.split(".")[0]

    if x.endswith("Z"):
        x = x[:-1]

    return datetime.strptime(x, "%Y-%m-%dT%H:%M:%S")


def _rename_file(src: str, dest: str):
    try:
        os.rename(src, dest)
    except OSError:
        try:
            # If renaming fails, try copying
            shutil.copy(src, dest)
            os.remove(src)  # Remove the original file after copying
        except Exception as e:
            raise RuntimeError(
                f"Cannot move temporary file for '{src}' to its destination '{dest}': {e}."
            ) from e


def _download_and_rename_file(url: str, dest: str):
    tmp = tempfile.NamedTemporaryFile(dir=os.path.dirname(dest), delete=False).name
    req = requests.get(url, stream=True, verify=REQUESTS_MOD["verify"])

    with open(tmp, "wb") as f:
        for chunk in req.iter_content():
            f.write(chunk)

    _rename_file(tmp, dest)


IS_LOCKED = {"locks": {}}


def _acquire_lock(cache: str, project: str, asset: str, version: str):
    _key = f"{project}/{asset}/{version}"

    if _key in IS_LOCKED["locks"] and IS_LOCKED["locks"][_key] is None:
        _path = os.path.join(cache, "status", project, asset, version)
        os.makedirs(os.path.dirname(_path), exist_ok=True)

        _lock = FileLock(_path + ".LOCK")
        _lock.acquire()
        IS_LOCKED["locks"][_key] = _lock


def _release_lock(project: str, asset: str, version: str):
    _key = f"{project}/{asset}/{version}"

    if _key in IS_LOCKED["locks"] and IS_LOCKED["locks"][_key] is not None:
        _lock = IS_LOCKED["locks"][_key]
        _lock.release()
        del IS_LOCKED["locks"][_key]


def _sanitize_path(x):
    if os.name == "nt":
        x = re.sub(r"\\\\", "/", x)

    x = re.sub(r"//+", "/", x)
    return x


def _sanitize_uploaders(uploaders: list):
    for current in uploaders:
        if "until" in current:
            _cur_until = current["until"]
            if isinstance(_cur_until, str):
                _cur_until = _cast_datetime(_cur_until)

            current["until"] = _cur_until.isoformat().replace("+00:00", "Z")

    return uploaders


# from https://stackoverflow.com/questions/15411967/how-can-i-check-if-code-is-executed-in-the-ipython-notebook
def is_notebook() -> bool:
    try:
        shell = get_ipython().__class__.__name__
        if shell == "ZMQInteractiveShell":
            return True  # Jupyter notebook or qtconsole
        elif shell == "TerminalInteractiveShell":
            return False  # Terminal running IPython
        else:
            return False  # Other type (?)
    except NameError:
        return False  # Probably standard Python interpreter


# from https://stackoverflow.com/questions/6108330/checking-for-interactive-shell-in-a-python-script
def _is_interactive():
    import sys

    return sys.__stdin__.isatty() or is_notebook()
