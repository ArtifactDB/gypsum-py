from urllib.parse import quote_plus

import requests

from ._utils import _remove_slash_url, _sanitize_uploaders
from .auth import access_token
from .fetch_operations import fetch_permissions
from .rest_url import rest_url

__author__ = "Jayaram Kancherla"
__copyright__ = "Jayaram Kancherla"
__license__ = "MIT"


def set_quota(
    project: str,
    baseline: int = None,
    growth_rate: int = None,
    year: int = None,
    url: str = rest_url(),
    token: str = None,
):
    """
    Set the quota for a project.

    See Also:
        :py:func:`~gypsum_client.fetch_operations.fetch_quota`,
        to fetch the usage details.

    Example:

        .. code-block:: python

            create_project("test-Py-quota", owners=["jkanche"])

            set_quota(
                "test-Py-quota",
                baseline=1234,
                growth_rate=5678,
                year=2020
            )


    Args:
        project:
            The project name.

        baseline:
            Baseline quote, in bytes.
            If `None`, no change is made.

        growth_rate:
            Expected annual growth rate, in bytes.
            If `None`, no change is made.

        year:
            Year of project creation.
            If `None`, no change is made.

        url:
            URL of the gypsum REST API.

        token:
            GitHub access token to authenticate to the gypsum REST API.
    """

    if token is None:
        token = access_token()

    url = _remove_slash_url(url)

    body = {}
    if baseline is not None:
        body["baseline"] = baseline

    if growth_rate is not None:
        body["growth_rate"] = growth_rate

    if year is not None:
        body["year"] = year

    endpoint = f"{url}/quota/{quote_plus(project)}"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    req = requests.put(endpoint, json=body, headers=headers)

    try:
        req.raise_for_status()
    except Exception as e:
        raise Exception(
            f"Failed to set quota, {req.status_code} and reason: {req.text}."
        ) from e


def set_permissions(
    project: str,
    owners: str = None,
    uploaders: str = None,
    append: bool = True,
    url: str = rest_url(),
    token: str = None,
):
    """
    Set the owner and uploader permissions for a project.

    See Also:
        :py:func:`~gypsum_client.fetch_operations.fetch_permission`,
        to fetch the permissions for a project.

    Example:

        .. code-block:: python

            create_project("test-Py-perms", owners=["jkanche"])

            until = (
                (datetime.now() + timedelta(seconds=1000000))
                .replace(microsecond=0)
            )

            set_permissions(
                "test-Py-perms",
                owners=["LTLA"],
                uploaders=[{"id": "LTLA", "until": until}]
            )

    Args:
        project:
            The project name.

        owners:
            List of GitHub users or organizations that are owners of this
            project.

            If `None`, no change is made.

        uploaders:
            List of authorized uploaders for this project.

            If `None`, no change is made.

        append:
            Whether to append owners and uploaders to the existing ones.

            If `False`, the provided owners and uploaders replace the existing values.

        url:
            URL of the gypsum REST API.

        token:
            GitHub access token to authenticate to the gypsum REST API.
    """
    if token is None:
        token = access_token()

    url = _remove_slash_url(url)

    perms = {}
    if append is True:
        old_perms = fetch_permissions(project, url=url)

        if owners is not None:
            perms["owners"] = list(set(old_perms["owners"]).union(owners))

        if uploaders is not None:
            perms["uploaders"] = old_perms["uploaders"] + uploaders
    else:
        if owners is not None:
            perms["owners"] = owners

        if uploaders is not None:
            perms["uploaders"] = uploaders

    if "uploaders" in perms:
        perms["uploaders"] = _sanitize_uploaders(perms["uploaders"])

    endpoint = f"{url}/permissions/{quote_plus(project)}"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    req = requests.put(endpoint, json=perms, headers=headers)

    try:
        req.raise_for_status()
    except Exception as e:
        raise Exception(
            f"Failed to set permissions, {req.status_code} and reason: {req.text}."
        ) from e
