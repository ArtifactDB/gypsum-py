from typing import List
from urllib.parse import quote_plus

import requests

from ._utils import _remove_slash_url, _rest_url, _sanitize_uploaders
from .auth import access_token
from .config import REQUESTS_MOD

__author__ = "Jayaram Kancherla"
__copyright__ = "Jayaram Kancherla"
__license__ = "MIT"


def create_project(
    project: str,
    owners: List[str],
    uploaders: List[str] = [],
    baseline: int = None,
    growth_rate: int = None,
    year: int = None,
    url: str = _rest_url(),
    token: str = None,
):
    """Create a new project with the associated permissions.

    Args:
        project:
            Project name.

        owners:
            List of GitHub users or organizations that are owners of this
            project.

        uploaders:
            List of authorized uploaders for this project.
            Defaults to an empty list.

            Checkout :py:func:`~gypsum_client.fetch_assets.fetch_permissions`
            for more info.

        baseline:
            Baseline quote in bytes.

        growth_rate:
            Expected annual growth rate in bytes.

        year:
            Year of project creation.

        url:
            URL to the gypsum REST API.

        token:
            GitHub access token to authenticate with the gypsum REST API.

    Returns:
        True if project is successfully created.
    """
    url = _remove_slash_url(url)
    uploaders = _sanitize_uploaders(uploaders) if uploaders is not None else []

    if token is None:
        token = access_token()

    quota = {}
    if baseline is not None:
        quota["baseline"] = baseline

    if growth_rate is not None:
        quota["growth_rate"] = growth_rate

    if year is not None:
        quota["year"] = year

    body = {"permissions": {"owners": owners, "uploaders": uploaders}}
    if len(quota) > 0:
        body["quota"] = quota

    req = requests.post(
        f"{url}/create/{quote_plus(project)}",
        json=body,
        headers={"Authorization": "Bearer " + token},
        verify=REQUESTS_MOD["verify"],
    )
    try:
        req.raise_for_status()
    except Exception as e:
        raise Exception(
            f"Failed to create a project, {req.status_code} and reason: {req.text}"
        ) from e

    return True
