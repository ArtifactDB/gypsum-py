from urllib.parse import quote_plus

import requests

from ._utils import (
    _remove_slash_url,
    _rest_url,
)
from .auth import access_token

__author__ = "Jayaram Kancherla"
__copyright__ = "Jayaram Kancherla"
__license__ = "MIT"


def approve_probation(
    project: str, asset: str, version: str, url: str = _rest_url(), token: str = None
):
    """Approve a probational upload.

    This removes the ``on_probation`` tag from the uploaded version.

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
    """

    if token is None:
        token = access_token()

    url = _remove_slash_url(url)
    _key = f"{quote_plus(project)}/{quote_plus(asset)}/{quote_plus(version)}"
    req = requests.post(
        f"{url}/probation/approve/{_key}",
        headers={"Authorization": f"Bearer {token}"},
    )

    try:
        req.raise_for_status()
    except Exception as e:
        raise Exception(
            f"Failed to approve probation, {req.status_code} and reason: {req.text}."
        ) from e


def reject_probation(
    project: str, asset: str, version: str, url: str = _rest_url(), token: str = None
):
    """Reject a probational upload.

    This removes all files associated with that version.

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
    """

    if token is None:
        token = access_token()

    url = _remove_slash_url(url)
    _key = f"{quote_plus(project)}/{quote_plus(asset)}/{quote_plus(version)}"
    req = requests.post(
        f"{url}/probation/reject/{_key}",
        headers={"Authorization": f"Bearer {token}"},
    )

    try:
        req.raise_for_status()
    except Exception as e:
        raise Exception(
            f"Failed to reject probation, {req.status_code} and reason: {req.text}."
        ) from e
