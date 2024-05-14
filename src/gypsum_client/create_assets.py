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
    growth: int = None,
    year: int = None,
    url=_rest_url(),
    token=access_token(),
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

        growth:
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

    quota = {}
    if baseline is not None:
        quota["baseline"] = baseline
    if growth is not None:
        quota["growth_rate"] = growth
    if year is not None:
        quota["year"] = year

    body = {"permissions": {"owners": owners, "uploaders": uploaders}}
    if quota:
        body["quota"] = quota

    req = requests.post(
        f"{url}/create/{quote_plus(project)}",
        json=body,
        headers={"Authorization": "Bearer " + token},
        verify=REQUESTS_MOD["verify"],
    )
    req.raise_for_status()

    return True
