import atexit
import json
import os
import re
import shutil
from multiprocessing import Pool
from typing import Optional

from ._utils import (
    BUCKET_CACHE_NAME,
    _acquire_lock,
    _release_lock,
    _sanitize_path,
    _save_file,
)
from .cache_directory import cache_directory
from .config import REQUESTS_MOD
from .list_operations import list_files
from .resolve_links import resolve_links
from .rest_url import rest_url

__author__ = "Jayaram Kancherla"
__copyright__ = "Jayaram Kancherla"
__license__ = "MIT"


def _save_file_wrapper(args):
    x, project, asset, version, destination, overwrite, url, verify = args
    path = os.path.join(project, asset, version, x)
    dest = os.path.join(destination, x)
    _save_file(path=path, destination=dest, overwrite=overwrite, url=url, verify=verify)


def save_version(
    project: str,
    asset: str,
    version: str,
    cache_dir: Optional[str] = cache_directory(),
    overwrite: bool = False,
    relink: bool = True,
    concurrent: int = 1,
    url: str = rest_url(),
) -> str:
    """Download all files associated with a version of an asset
    of a project from the gypsum bucket.

    See Also:

        :py:func:`~.save_file`, to save a single file.

    Example:

        .. code-block:: python

            out <- save_version("test-R", "basic", "v1")

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

        relink:
            Whether links should be resolved, see :py:func:`~resolve_links`.
            Defaults to True.

        concurrent:
            Number of concurrent downloads.
            Defaults to 1.

    Returns:
        Path to the local directory where the files are downloaded to.
    """

    _acquire_lock(cache_dir, project, asset, version)

    def release_lock_wrapper():
        _release_lock(project, asset, version)

    atexit.register(release_lock_wrapper)
    destination = os.path.join(cache_dir, BUCKET_CACHE_NAME, project, asset, version)

    # If this version's directory was previously cached in its complete form, we skip it.
    completed = os.path.join(cache_dir, "status", project, asset, version, "COMPLETE")
    if not os.path.exists(completed) or overwrite:
        listing = list_files(project, asset, version, url=url)

        if concurrent <= 1:
            for file in listing:
                _save_file_wrapper(
                    (
                        file,
                        project,
                        asset,
                        version,
                        destination,
                        overwrite,
                        url,
                        REQUESTS_MOD["verify"],
                    )
                )
        else:
            _args = [
                (
                    file,
                    project,
                    asset,
                    version,
                    destination,
                    overwrite,
                    url,
                    REQUESTS_MOD["verify"],
                )
                for file in listing
            ]
            with Pool(concurrent) as pool:
                pool.map(_save_file_wrapper, _args)

        if relink:
            resolve_links(
                project,
                asset,
                version,
                cache_dir=cache_dir,
                overwrite=overwrite,
                url=url,
            )

        # Marking it as complete.
        os.makedirs(os.path.dirname(completed), exist_ok=True)
        with open(completed, "w"):
            pass

    return destination


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
    cache_dir: Optional[str] = cache_directory(),
    overwrite: bool = False,
    url: str = rest_url(),
):
    """Save a file from a version of a project asset.

    Download a file from the gypsum bucket, for a version of
    an asset of a project.

    See Also:

        :py:func:`~.save_version`, to save all files associated
        with a version.

    Example:

        .. code-block:: python

            out <- save_version("test-R", "basic", "v1", "blah.txt")


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
                    raise ValueError(
                        f"Failed to resolve link for '{path}': {e}."
                    ) from e

    return destination
