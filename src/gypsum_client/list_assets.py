import requests

from ._utils import _list_for_prefix, _rest_url
from .config import REQUESTS_MOD

__author__ = "Jayaram Kancherla"
__copyright__ = "Jayaram Kancherla"
__license__ = "MIT"


def list_projects(url: str = _rest_url()) -> list:
    """List all projects in the gypsum backend.

    Args:
        url:
            URL to the gypsum compatible API.


    Returns:
        List of project names.
    """
    return _list_for_prefix(prefix=None, url=url)


def list_assets(project: str, url: str = _rest_url()) -> list:
    """List all assets in a project.

    Args:
        project:
            Project name.

        url:
            URL to the gypsum compatible API.

    Returns:
        List of asset names.
    """
    return _list_for_prefix(f"{project}/", url=url)


def list_versions(project: str, asset: str, url=_rest_url()) -> list:
    """List all versions for a project asset.

    Args:
        project:
            Project name.

        asset:
            Asset name.

        url:
            URL to the gypsum compatible API.

    Returns:
        List of versions.
    """
    return _list_for_prefix(f"{project}/{asset}/", url=url)


def list_files(
    project: str,
    asset: str,
    version: str,
    prefix: str = None,
    include_dot: bool = True,
    url: str = _rest_url(),
) -> list:
    """List all files for a specified version of a project and asset.

    Args:
        project:
            Project name.

        asset:
            Asset name.

        version:
            Version name.

        prefix:
            Prefix for the object key.

            If provided. a file is only listed if its object key starts with
            ``{project}/{asset}/{version}/{prefix}``.

            Defaults to None and all associated files with this version of the
            asset in the specified project are listed.

        include_dot:
            Whether to list files with ``..`` in their names.

        url:
            URL to the gypsum compatible API.

    Returns:
        List of relative paths of files associated with the versioned asset.
    """
    _prefix = f"{project}/{asset}/{version}/"
    _trunc = len(_prefix)
    if prefix is not None:
        _prefix = f"{_prefix}{prefix}"

    req = requests.get(
        f"{url}/list",
        params={"recursive": "true", "prefix": _prefix},
        verify=REQUESTS_MOD["verify"],
    )
    req.raise_for_status()
    resp = req.json()

    resp = [val[_trunc:] for val in resp]

    if prefix is not None:
        resp = [val for val in resp if val.startswith(prefix)]

    if include_dot is False:
        resp = [val for val in resp if not val.startswith("..")]

    return resp
