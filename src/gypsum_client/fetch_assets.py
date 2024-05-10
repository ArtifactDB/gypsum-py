from typing import Optional

import requests

from ._utils import _cache_directory, _fetch_cacheable_json, _fetch_json, _rest_url

__author__ = "Jayaram Kancherla"
__copyright__ = "Jayaram Kancherla"
__license__ = "MIT"


def fetch_latest(project: str, asset: str, url=_rest_url()) -> str:
    """Fetch the latest version of a project's asset.

    Args:
        project:
            Project name.

        asset:
            Asset name.

        url:
            URL to the gypsum compatible API.

    Returns:
        Latest version of the project.
    """
    resp = _fetch_json(f"{project}/{asset}/..latest", url=url)
    return resp["version"]


def fetch_manifest(
    project, asset, version, cache=_cache_directory(), overwrite=False, url=_rest_url()
):
    """Fetch the manifest for a version of an asset of a project.

    Args:
        project:
            Project name.

        asset:
            Asset name.

        version:
            Version name.

        cache:
            Path to the cache directory.

        overwrite:
            Whether to overwrite existing file in cache.

        url:
            URL to the gypsum compatible API.

    Returns:
        _description_
    """
    return _fetch_cacheable_json(
        project, asset, version, "..manifest", url=url, cache=cache, overwrite=overwrite
    )
