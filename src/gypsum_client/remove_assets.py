from urllib.parse import quote_plus

import requests

from ._utils import _remove_slash_url, _rest_url
from .auth import access_token

__author__ = "Jayaram Kancherla"
__copyright__ = "Jayaram Kancherla"
__license__ = "MIT"


def remove_asset(
    project: str, asset: str, url: str = _rest_url(), token: str = access_token()
):
    """Remove an asset of a project from the gypsum backend.

    Args:
        project:
            Project name.

        asset:
            Asset name.

        url:
            URL of the gypsum REST API.

        token:
            GitHub access token to authenticate to the gypsum REST API.

    Returns:
        True if asset was successfully removed.
    """

    _key = f"{quote_plus(project)}/{quote_plus(asset)}"
    _request_removal(_key, url=url, token=token)

    return True


def remove_project(project: str, url: str = _rest_url(), token: str = access_token()):
    """Remove a project from the gypsum backend.

    Args:
        project:
            Project name.

        url:
            URL of the gypsum REST API.

        token:
            GitHub access token to authenticate to the gypsum REST API.

    Returns:
        True if the project was successfully removed.
    """

    _key = f"{quote_plus(project)}"
    _request_removal(_key, url=url, token=token)

    return True


def remove_version(
    project: str,
    asset: str,
    version: str,
    url: str = _rest_url(),
    token: str = access_token(),
):
    """Remove a project from the gypsum backend.

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
        )

    return True
