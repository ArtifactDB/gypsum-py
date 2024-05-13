import atexit
import os
from multiprocessing import Pool
from typing import Optional

from ._utils import (
    BUCKET_CACHE_NAME,
    _acquire_lock,
    _cache_directory,
    _release_lock,
    _save_file,
)
from .list_assets import list_files
from .resolve_links import resolve_links

__author__ = "Jayaram Kancherla"
__copyright__ = "Jayaram Kancherla"
__license__ = "MIT"


def save_version(
    project: str,
    asset: str,
    version: str,
    cache_dir: Optional[str] = None,
    overwrite: bool = False,
    relink: bool = True,
    concurrent: int = 1,
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
        listing = list_files(project, asset, version)

        def save_file(x):
            path = os.path.join(project, asset, version, x)
            dest = os.path.join(destination, x)
            _save_file(path=path, destination=dest, overwrite=overwrite)

        if concurrent == 1:
            for file in listing:
                save_file(file)
        else:
            with Pool(concurrent) as pool:
                pool.map(save_file, listing)

        if relink:
            resolve_links(project, asset, version, cache=cache_dir, overwrite=overwrite)

        # Marking it as complete.
        os.makedirs(os.path.dirname(completed), exist_ok=True)
        with open(completed, "w"):
            pass

    return destination
