from urllib.parse import quote_plus

import requests

from ._utils import (
    _remove_slash_url,
)
from .auth import access_token
from .rest_url import rest_url

__author__ = "Jayaram Kancherla"
__copyright__ = "Jayaram Kancherla"
__license__ = "MIT"


def refresh_latest(
    project: str, asset: str, url: str = rest_url(), token: str = None
) -> str:
    """Refresh the latest version.

    Recompute the latest version of a project's asset.
    This is useful on rare occasions where multiple simultaneous
    uploads cause the latest version to be slightly out of sync.

    See Also:
        :py:func:`~gypsum_client.fetch_operations.fetch_latest`,
        to fetch the latest version without recomputing.

    Example:

        .. code-block:: python

            ver = refresh_latest("test-R", "basic")

    Args:
        project:
            Project name.

        asset:
            Asset name.

        url:
            URL of the gypsum REST API.

        token:
            GitHub access token to authenticate to the gypsum REST API.

    Return:
        A string containing the latest version.
    """

    if token is None:
        token = access_token()

    url = _remove_slash_url(url)
    _key = f"{quote_plus(project)}/{quote_plus(asset)}"
    req = requests.post(
        f"{url}/refresh/latest/{_key}",
        headers={"Authorization": f"Bearer {token}"},
    )

    try:
        req.raise_for_status()
    except Exception as e:
        raise Exception(
            f"Failed to refresh latest version, {req.status_code} and reason: {req.text}"
        ) from e

    return req.json()["version"]


def refresh_usage(project: str, url: str = rest_url(), token: str = None) -> int:
    """Refresh the usage quota of a project.

    Recompute the usage of a project.
    This is useful on rare occasions where multiple simultaneous
    uploads cause the usage calculations to be out of sync.

    See Also:
        :py:func:`~gypsum_client.fetch_operations.fetch_usage`,
        to fetch the usage without recomputing.

    Example:

        .. code-block:: python

            ver = refresh_usage("test-R", "basic")

    Args:
        project:
            Project name.

        url:
            URL of the gypsum REST API.

        token:
            GitHub access token to authenticate to the gypsum REST API.

    Returns:
        The total quota usage of this project, in bytes.
    """

    if token is None:
        token = access_token()

    url = _remove_slash_url(url)
    _key = f"{quote_plus(project)}"
    req = requests.post(
        f"{url}/refresh/usage/{_key}",
        headers={"Authorization": f"Bearer {token}"},
    )

    try:
        req.raise_for_status()
    except Exception as e:
        raise Exception(
            f"Failed to refresh quota usage, {req.status_code} and reason: {req.text}"
        ) from e

    return req.json()["total"]
