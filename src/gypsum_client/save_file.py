import atexit
import json
import os
import re
import shutil
from typing import Optional

from ._utils import (
    BUCKET_CACHE_NAME,
    _acquire_lock,
    _cache_directory,
    _release_lock,
    _rest_url,
    _sanitize_path,
    _save_file,
)

__author__ = "Jayaram Kancherla"
__copyright__ = "Jayaram Kancherla"
__license__ = "MIT"


def _resolve_single_link(
    project: str,
    asset: str,
    version: str,
    path: str,
    cache: str,
    overwrite: bool,
    url: str,
) -> Optional[str]:
    if "/" in path:
        lpath = f"{os.path.dirname(path)}/..links"
    else:
        lpath = "..links"

    lobject = f"{project}/{asset}/{version}/{lpath}"
    ldestination = os.path.join(
        cache, BUCKET_CACHE_NAME, project, asset, version, lpath
    )

    _saved = _save_file(
        lobject, ldestination, overwrite=overwrite, url=url, error=False
    )

    if not _saved:
        return None

    with open(ldestination, "r") as f:
        link_info = json.load(f)

    base = re.sub(r".*/", "", path)

    if base not in link_info:
        return None

    target = link_info[base]
    if "ancestor" in target:
        target = target["ancestor"]

    tobject = (
        f"{target['project']}/{target['asset']}/{target['version']}/{target['path']}"
    )
    tdestination = os.path.join(
        cache,
        BUCKET_CACHE_NAME,
        target["project"],
        target["asset"],
        target["version"],
        target["path"],
    )

    _save_file(tobject, tdestination, overwrite=overwrite, url=url)
    return tdestination


def save_file(
    project: str,
    asset: str,
    version: str,
    path: str,
    cache_dir: Optional[str] = None,
    overwrite: bool = False,
    url: str = _rest_url(),
):
    """Save a file from a version of a project asset.

    Download a file from the gypsum bucket, for a version of
    an asset of a project.

    Args:
        project:
            Project name.

        asset:
            Asset name.

        version:
            Version name.

        path:
            Suffix of the object key for the file of interest,
            i.e., the relative ``path`` inside the version's `
            `subdirectory``.

            The full object key is defined as
            ``{project}/{asset}/{version}/{path}``.

        cache_dir:
            Path to the cache directory.

        overwrite:
            Whether to overwrite existing file in cache.

        url:
            URL to the gypsum compatible API.

    Returns:
        The destintion file path where the file is downloaded to in the local
        file system.
    """
    cache_dir = _cache_directory(cache_dir)

    _acquire_lock(cache_dir, project, asset, version)

    def release_lock_wrapper():
        _release_lock(project, asset, version)

    atexit.register(release_lock_wrapper)

    object_key = f"{project}/{asset}/{version}/{_sanitize_path(path)}"
    destination = os.path.join(
        cache_dir, BUCKET_CACHE_NAME, project, asset, version, path
    )

    found = _save_file(
        object_key, destination, overwrite=overwrite, url=url, error=False
    )

    if not found:
        link = _resolve_single_link(
            project, asset, version, path, cache_dir, overwrite=overwrite, url=url
        )

        if link is None:
            raise ValueError(f"'{path}' does not exist in the bucket.")

        try:
            os.link(link, destination)
        except Exception:
            try:
                os.symlink(link, destination)
            except Exception:
                try:
                    shutil.copy(link, destination)
                except Exception as e:
                    raise ValueError(f"Failed to resolve link for '{path}': {e}.")

    return destination
