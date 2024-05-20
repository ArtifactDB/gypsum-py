"""Clone a version's directory structure.

Cloning of a versioned asset involves creating a directory at the destination
that has the same contents as the corresponding project-asset-version directory.
All files in the specified version are represented as symlinks from the
destination to the corresponding file in the cache.
The idea is that, when the destination is used in
:py:func:`~gypsum_client.prepare_directory_for_upload.prepare_directory_upload`,
the symlinks are converted into upload links, i.e., ``links=`` in
:py:func:`~gypsum_client.upload_api_operations.start_upload`.
This allows users to create new versions very cheaply as duplicate files
are not uploaded to/stored in the backend.

Users can more-or-less do whatever they want inside the cloned destination,
but they should treat the symlink targets as read-only.
That is, they should not modify the contents of the linked-to file, as these
refer to assumed-immutable files in the cache.
If a file in the destination needs to be modified, the symlink should be
deleted and replaced with an actual file;
this avoids mutating the cache and it ensures that
:py:func:`~gypsum_client.prepare_directory_for_upload.prepare_directory_upload`
recognizes that a new file actually needs to be uploaded.

Advanced users can set ``download=False``, in which case symlinks are created
even if their targets are not present in the cache.
In such cases, the destination should be treated as write-only due to the
potential presence of dangling symlinks.
This mode is useful for uploading a new version of an asset without
downloading the files from the existing version,
assuming that the modifications associated with the former can be
achieved without reading any of the latter.

On Windows, the user may not have permissions to create symbolic links,
so the function will transparently fall back to creating hard links or
copies instead.
This precludes any optimization by prepare_directory_upload as the hard
links/copies cannot be converted into upload links.
It also assumes that download=True as dangling links/copies cannot be created.
"""

import errno
import os
import shutil

from ._utils import BUCKET_CACHE_NAME
from .cache_directory import cache_directory
from .fetch_operations import fetch_manifest
from .rest_url import rest_url
from .save_operations import save_version

__author__ = "Jayaram Kancherla"
__copyright__ = "Jayaram Kancherla"
__license__ = "MIT"


def clone_version(
    project: str,
    asset: str,
    version: str,
    destination: str,
    download: bool = True,
    cache_dir: str = cache_directory(),
    url: str = rest_url(),
    **kwargs,
):
    """Clone a version's directory structure.

    Clone the directory structure for a versioned asset into a separate location.
    This is typically used to prepare a new version for a lightweight upload.

    See Also:
        :py:func:`~gypsum_client.prepare_directory_for_upload.prepare_directory_upload`,
        to prepare an upload based on the directory contents.

    Example:

        .. code-block:: python

            import tempfile

            cache = tempfile.mkdtemp()
            dest = tempfile.mkdtemp()

            clone_version("test-R", "basic", "v1", destination=dest, cache_dir=cache)

    Args:
        project:
            Project name.

        asset:
            Asset name.

        version:
            Version name.

        cache_dir:
            Path to the cache directory.

        destination:
            Destination directory at which to create the clone.

        download:
            Whether the version's files should be downloaded first.
            This can be set to `False` to create a clone without
            actually downloading any of the version's files.
            Defaults to True.

        url:
            URL of the gypsum REST API.

        **kwargs:
            Further arguments to pass to
            :py:func:`~gypsum_client.save_assets.save_version`.

            Only used if ``download`` is `True`.
    """
    if download:
        save_version(project, asset, version, cache_dir=cache_dir, url=url, **kwargs)

    final_cache = os.path.join(cache_dir, BUCKET_CACHE_NAME, project, asset, version)
    listing = fetch_manifest(project, asset, version, cache_dir=cache_dir, url=url)
    os.makedirs(destination, exist_ok=True)

    # Normalize final_cache path
    final_cache = os.path.abspath(final_cache)

    # Create symlinks back to the cache
    for file_name in listing.keys():
        dpath = os.path.join(destination, file_name)
        os.makedirs(os.path.dirname(dpath), exist_ok=True)
        target = os.path.join(final_cache, file_name)

        try:
            os.symlink(target, dpath)
        except OSError as e:
            if e.errno == errno.EEXIST:
                os.remove(dpath)
                os.symlink(target, dpath)
            elif os.name == "nt":
                try:
                    os.link(target, dpath)
                except OSError:
                    shutil.copy(target, dpath)
            else:
                raise RuntimeError(
                    f"failed to create a symbolic link to '{target}' at '{dpath}'."
                ) from e
