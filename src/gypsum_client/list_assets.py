from typing import Optional

import requests

from ._utils import _list_for_prefix, _rest_url

__author__ = "Jayaram Kancherla"
__copyright__ = "Jayaram Kancherla"
__license__ = "MIT"


def list_projects(prefix: Optional[str] = None, url: str = _rest_url()):
    return _list_for_prefix(prefix, url)


def list_assets(project: str, url: str = _rest_url()):
    return _list_for_prefix(f"{project}/", url=url)


def list_versions(project: str, asset: str, url=_rest_url()):
    return _list_for_prefix(f"{project}/{asset}/", url=url)


def list_files(
    project: str,
    asset: str,
    version: str,
    prefix: str = None,
    include_dot: bool = True,
    url: str = _rest_url(),
):
    _prefix = f"{project}/{asset}/{version}/"
    if prefix is not None:
        _prefix = f"{_prefix}{prefix}"

    req = requests.get(f"{url}/list", params={"recursive": True, "prefix": _prefix})
    req.raise_for_status()

    resp = req.json()
    resp = [val for val in resp if val.endswith("/")]

    if prefix is not None:
        resp = [val.startswith(prefix) for val in resp]

    if include_dot is False:
        resp = [val for val in resp if not val.startswith("..")]

    return resp
