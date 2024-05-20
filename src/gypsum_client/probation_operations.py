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


def approve_probation(
    project: str, asset: str, version: str, url: str = rest_url(), token: str = None
):
    """Approve a probational upload.

    This removes the ``on_probation`` tag from the uploaded version.

    See Also:
        :py:func:`~gypsum_client.upload_api_operations.start_upload`,
        to specify probational upload.

        :py:func:`~.reject_probation`,
        to reject the probational upload..

    Example:

        .. code-block:: python

            init = start_upload(
                project="test-Py",
                asset="probation",
                version="v1",
                files=[],
                probation=True
            )

            complete_upload(init)
            approve_probation("test-Py", "probation", "v1")

            # Cleanup if this is just for testing
            remove_asset("test-Py", "probation")

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
    project: str, asset: str, version: str, url: str = rest_url(), token: str = None
):
    """Reject a probational upload.

    This removes all files associated with that version.

    See Also:
        :py:func:`~gypsum_client.upload_api_operations.start_upload`,
        to specify probational upload.

        :py:func:`~.approve_probation`,
        to approve the probational upload..

    Example:

        .. code-block:: python

            init = start_upload(
                project="test-Py",
                asset="probation",
                version="v1",
                files=[],
                probation=True
            )

            complete_upload(init)
            reject_probation("test-Py", "probation", "v1")

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
