import atexit
import os
import shutil
from typing import Optional

from ._utils import (
    BUCKET_CACHE_NAME,
    _acquire_lock,
    _release_lock,
)
from .cache_directory import cache_directory
from .fetch_operations import fetch_manifest
from .rest_url import rest_url

__author__ = "Jayaram Kancherla"
__copyright__ = "Jayaram Kancherla"
__license__ = "MIT"


def resolve_links(
    project: str,
    asset: str,
    version: str,
    cache_dir: Optional[str] = cache_directory(),
    overwrite: str = False,
    url: str = rest_url(),
):
    """Resolve links in the cache directory.

    Create hard links (or copies, if filesystem links
    are not supported) for linked-from files to their
    link destinations.

    Example:

        .. code-block:: python

            cache = tempfile()

            save_version("test-R", "basic", "v3", relink=False, cache_dir=cache)
            list_files(cache_dir, recursive=True, all_files=True)

            resolve_links("test-R", "basic", "v3", cache_dir=cache)

    Args:
        project:
            Project name.

        asset:
            Asset name.

        version:
            Version name.

        cache_dir:
            Path to the cache directory.

        overwrite:
            Whether to overwrite existing file in cache.

        url:
            URL to the gypsum compatible API.

    Returns:
        True if all links are resolved.
    """
    from .save_operations import save_file

    _acquire_lock(cache_dir, project, asset, version)

    def release_lock_wrapper():
        _release_lock(project, asset, version)

    atexit.register(release_lock_wrapper)

    # destination = os.path.join(cache_dir, BUCKET_CACHE_NAME, project, asset, version)
    manifests = {}

    self_manifest = fetch_manifest(
        project, asset, version, cache_dir=cache_dir, url=url
    )
    manifests["/".join([project, asset, version])] = self_manifest

    for kmf in self_manifest.keys():
        entry = self_manifest[kmf]
        if entry.get("link") is None:
            continue

        old_loc = os.path.join(project, asset, version, kmf)
        if os.path.exists(old_loc) and not overwrite:
            continue

        link_data = entry["link"]
        if link_data.get("ancestor") is not None:
            link_data = link_data["ancestor"]

        out = save_file(
            link_data["project"],
            link_data["asset"],
            link_data["version"],
            link_data["path"],
            cache_dir=cache_dir,
            url=url,
            overwrite=overwrite,
        )
        old_path = os.path.join(cache_dir, BUCKET_CACHE_NAME, old_loc)

        try:
            os.unlink(old_path)
        except Exception:
            pass

        os.makedirs(os.path.dirname(old_path), exist_ok=True)

        try:
            os.link(out, old_path)
        except Exception:
            try:
                os.symlink(out, old_path)
            except Exception:
                try:
                    shutil.copy(out, old_path)
                except Exception as e:
                    raise ValueError(f"Failed to resolve link for '{kmf}': {e}") from e

    return True
