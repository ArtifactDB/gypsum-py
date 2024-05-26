"""Prepare to upload a directory's contents.

Files in `directory` (that are not symlinks) are used as
regular uploads, i.e., `files=` in
:py:func:`~gypsum_client.upload_api_operations.start_upload`.

If `directory` contains a symlink to a file in `cache`,
we assume that it points to a file that was previously downloaded
by, e.g., :py:func:`~gypsum_client.upload_api_operations.save_file` or
:py:func:`~gypsum_client.upload_api_operations.save_version`.
Thus, instead of performing a regular upload, we attempt to
create an upload link, i.e., ``links=`` in
:py:func:`~gypsum_client.upload_api_operations.start_upload`.
This is achieved by examining the destination path of the
symlink and inferring the link destination in the backend.
Note that this still works if the symlinks are dangling.

If a symlink cannot be converted into an upload link, it will
be used as a regular upload, i.e., the contents of the symlink
destination will be uploaded by
:py:func:`~gypsum_client.upload_api_operations.start_upload`.
In this case, an error will be raised if the symlink is dangling
as there is no file that can actually be uploaded.
If ``links="always"``, an error is raised instead upon symlink
conversion failure.

This function is intended to be used with
:py:func:`~gypsum_client.clone_operations.clone_version`,
which creates symlinks to files in `cache`.

See Also:
    :py:func:`~gypsum_client.upload_api_operations.start_upload`,
    to actually start the upload.

    :py:func:`~gypsum_client.clone_operations.clone_version`,
    to prepare the symlinks.

Example:

    .. code-block:: python

        import tempfile
        cache = tempfile.mkdtemp()
        dest = tempfile.mkdtemp()

        # Clone a project
        clone_version("test-R", "basic", "v1", destination=dest, cache_dir=cache)

        # Make some modification
        with open(os.path.join(dest, "heanna"), "w") as f:
            f.write("sumire")

        # Prepare the directory for upload
        prepped = prepare_directory_upload(dest, cache_dir=cache)
"""

import os
from typing import Literal

from ._utils import (
    BUCKET_CACHE_NAME,
    _sanitize_path,
)
from .cache_directory import cache_directory

__author__ = "Jayaram Kancherla"
__copyright__ = "Jayaram Kancherla"
__license__ = "MIT"


def prepare_directory_upload(
    directory: str,
    links: Literal["auto", "always", "never"] = "auto",
    cache_dir: str = cache_directory(),
) -> dict:
    """Prepare to upload a directory's contents.

    Prepare to upload a directory's contents via `start_upload`.
    This goes through the directory to list its contents and
    convert symlinks to upload links.

    Args:
        directory:
            Path to a directory, the contents of which are to be
            uploaded via :py:func:`~gypsum_client.start_upload.start_upload`.

        links:
            Indicate how to handle symlinks in `directory`.
            Must be one of the following:
            - "auto": Will attempt to convert symlinks into upload links.
            If the conversion fails, a regular upload is performed.
            - "always": Will attempt to convert symlinks into upload links.
            If the conversion fails, an error is raised.
            - "never": Will never attempt to convert symlinks into upload
            links. All symlinked files are treated as regular uploads.

        cache_dir:
            Path to the cache directory, used to convert symlinks into upload links.

    Returns:
        Dictionary containing:
        - `files`: list of strings to be used as `files=`
        in :py:func:`~gypsum_client.start_upload.start_upload`.
        - `links`: dictionary to be used as `links=` in
        :py:func:`~gypsum_client.start_upload.start_upload`.

    """
    _links_options = ["auto", "always", "never"]
    if links not in _links_options:
        raise ValueError(
            f"Invalid value for 'links': {links}. Must be one of {_links_options}."
        )

    out_files = []
    out_links = []

    cache_dir = _normalize_and_sanitize_path(cache_dir)
    if not cache_dir.endswith("/"):
        cache_dir += "/"

    for root, _, files in os.walk(directory):
        for name in files:
            rel_path = os.path.relpath(os.path.join(root, name), directory)

            if not os.path.islink(os.path.join(directory, rel_path)):
                out_files.append(rel_path)
                continue

            dest = os.readlink(os.path.join(directory, rel_path))

            if links == "never":
                if not os.path.exists(dest):
                    raise ValueError(
                        f"Cannot use a dangling link to '{dest}' as a regular upload."
                    )
                out_files.append(rel_path)
                continue

            dest = _normalize_and_sanitize_path(dest)
            dest_components = _match_path_to_cache(dest, cache_dir)

            if dest_components:
                out_links.append(
                    {
                        "from.path": rel_path,
                        "to.project": dest_components["project"],
                        "to.asset": dest_components["asset"],
                        "to.version": dest_components["version"],
                        "to.path": dest_components["path"],
                    }
                )
                continue

            if links == "always":
                raise ValueError(
                    f"Failed to convert symlink '{dest}' to an upload link."
                )
            elif not os.path.exists(dest):
                raise ValueError(
                    f"Cannot use a dangling link to '{dest}' as a regular upload."
                )

            out_files.append(rel_path)

    return {"files": out_files, "links": out_links}


def _normalize_and_sanitize_path(path: str) -> str:
    if os.path.exists(path):
        path = os.path.join(
            os.path.normpath(os.path.dirname(path)), os.path.basename(path)
        )
    return _sanitize_path(path)


def _match_path_to_cache(path: str, cache: str) -> dict:
    if not path.startswith(cache):
        return None

    remainder = path[len(cache) :]
    components = remainder.split("/")
    if len(components) <= 4 or components[0] != BUCKET_CACHE_NAME:
        return None

    return {
        "project": components[1],
        "asset": components[2],
        "version": components[3],
        "path": "/".join(components[4:]),
    }
