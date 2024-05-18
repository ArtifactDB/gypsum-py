import atexit
import os
from multiprocessing import Pool
from typing import Optional

from ._utils import (
    BUCKET_CACHE_NAME,
    _acquire_lock,
    _cache_directory,
    _release_lock,
    _rest_url,
    _save_file,
)
from .config import REQUESTS_MOD
from .list_assets import list_files
from .resolve_links import resolve_links

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
    cache_dir: Optional[str] = None,
    overwrite: bool = False,
    relink: bool = True,
    concurrent: int = 1,
    url: str = _rest_url(),
) -> str:
    """Download all files associated with a version of an asset
    of a project from the gypsum bucket.

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

    cache_dir = _cache_directory(cache_dir)
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
