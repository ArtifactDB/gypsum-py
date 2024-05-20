import requests

from ._utils import _list_for_prefix
from .config import REQUESTS_MOD
from .rest_url import rest_url

__author__ = "Jayaram Kancherla"
__copyright__ = "Jayaram Kancherla"
__license__ = "MIT"


def list_projects(url: str = rest_url()) -> list:
    """List all projects in the gypsum backend.

    Example:

        .. code-block:: python

            all_prjs = list_projects()

    Args:
        url:
            URL to the gypsum compatible API.

    Returns:
        List of project names.
    """
    return _list_for_prefix(prefix=None, url=url)


def list_assets(project: str, url: str = rest_url()) -> list:
    """List all assets in a project.

    Example:

        .. code-block:: python

            all_assets = list_assets("test-R")

    Args:
        project:
            Project name.

        url:
            URL to the gypsum compatible API.

    Returns:
        List of asset names.
    """
    return _list_for_prefix(f"{project}/", url=url)


def list_versions(project: str, asset: str, url: str = rest_url()) -> list:
    """List all versions for a project asset.

    Example:

        .. code-block:: python

            all_vers = list_versions("test-R", "basic")

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
    url: str = rest_url(),
) -> list:
    """List all files for a specified version of a project and asset.

    Example:

        .. code-block:: python

            all_files = list_files("test-R", "basic", "v1")

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
    try:
        req.raise_for_status()
    except Exception as e:
        raise Exception(
            f"Failed to list files in a project, {req.status_code} and reason: {req.text}"
        ) from e
    resp = req.json()

    resp = [val[_trunc:] for val in resp]

    if prefix is not None:
        resp = [val for val in resp if val.startswith(prefix)]

    if include_dot is False:
        resp = [val for val in resp if not val.startswith("..")]

    return resp
