from urllib.parse import quote_plus

import requests

from ._utils import _remove_slash_url
from .auth import access_token
from .rest_url import rest_url

__author__ = "Jayaram Kancherla"
__copyright__ = "Jayaram Kancherla"
__license__ = "MIT"


def remove_asset(project: str, asset: str, url: str = rest_url(), token: str = None):
    """Remove an asset of a project from the gypsum backend.

    See Also:
        :py:func:`~.remove_project`,
        to remove a project.

        :py:func:`~.remove_version`,
        to remove a specific version.

    Example:

        .. code-block:: python

            # Mock a project
            init = start_upload(
                project="test-Py-remove",
                asset="mock-remove",
                version="v1",
                files=[],
            )

            complete_upload(init)
            remove_asset("test-Py-remove", "mock-remove")

    Args:
        project:
            Project name.

        asset:
            Asset name.

        url:
            URL of the gypsum REST API.

        token:
            GitHub access token to authenticate to the gypsum REST API.
            The token must refer to a gypsum administrator account.

    Returns:
        True if asset was successfully removed.
    """

    if token is None:
        token = access_token()

    _key = f"{quote_plus(project)}/{quote_plus(asset)}"
    _request_removal(_key, url=url, token=token)

    return True


def remove_project(project: str, url: str = rest_url(), token: str = None):
    """Remove a project from the gypsum backend.

    See Also:
        :py:func:`~gypsum_client.create_operations.create_project`,
        to create a project.

        :py:func:`~.remove_asset`,
        to remove a specific asset.

        :py:func:`~.remove_version`,
        to remove a specific version.

    Example:

        .. code-block:: python

            create_project("test-Py-remove", owners=["jkanche"])
            remove_project("test-Py-remove")

    Args:
        project:
            Project name.

        url:
            URL of the gypsum REST API.

        token:
            GitHub access token to authenticate to the gypsum REST API.
            The token must refer to a gypsum administrator account.

    Returns:
        True if the project was successfully removed.
    """
    if token is None:
        token = access_token()

    _key = f"{quote_plus(project)}"
    _request_removal(_key, url=url, token=token)

    return True


def remove_version(
    project: str,
    asset: str,
    version: str,
    url: str = rest_url(),
    token: str = None,
):
    """Remove a project from the gypsum backend.

    See Also:
        :py:func:`~.remove_asset`,
        to remove a specific asset.

        :py:func:`~.remove_version`,
        to remove a specific version.

    Example:

        .. code-block:: python

            # Mock a project
            init = start_upload(
                project="test-Py-remove",
                asset="mock-remove",
                version="v1",
                files=[],
            )

            complete_upload(init)

            remove_version("test-Py-remove", "mock-remove", "v1")

    Args:
        project:
            Project name.

        asset:
            Asset name.

        version:
            Version name.

        url:
            URL of the gypsum REST API.

        token:
            GitHub access token to authenticate to the gypsum REST API.

    Returns:
        True if the version of the project was successfully removed.
    """

    if token is None:
        token = access_token()

    _key = f"{quote_plus(project)}/{quote_plus(asset)}/{quote_plus(version)}"
    _request_removal(_key, url=url, token=token)

    return True


def _request_removal(suffix: str, url: str, token: str):
    url = _remove_slash_url(url)

    headers = {}
    headers["Authorization"] = f"Bearer {token}"

    req = requests.delete(f"{url}/remove/{suffix}", headers=headers)
    try:
        req.raise_for_status()
    except Exception as e:
        raise Exception(
            f"Failed to remove assets in the project, {req.status_code} and reason: {req.text}"
        ) from e

    return True
