import os
from typing import Literal

from ._utils import (
    BUCKET_CACHE_NAME,
    _cache_directory,
    _sanitize_path,
)

__author__ = "Jayaram Kancherla"
__copyright__ = "Jayaram Kancherla"
__license__ = "MIT"


def prepare_directory_upload(
    directory: str,
    links: Literal["auto", "always", "never"] = "auto",
    cache_dir: str = _cache_directory(),
) -> dict:
    """Prepare to upload a directory's contents.

    Prepare to upload a directory's contents via `start_upload`.
    This goes through the directory to list its contents and
    convert symlinks to upload links.

    Files in `directory` (that are not symlinks) are used as
    regular uploads, i.e., `files=` in `start_upload`.

    If `directory` contains a symlink to a file in `cache`,
    we assume that it points to a file that was previously downloaded
    by, e.g., `save_file` or `save_version`.
    Thus, instead of performing a regular upload, we attempt to
    create an upload link, i.e., `links=` in `start_upload`.
    This is achieved by examining the destination path of the
    symlink and inferring the link destination in the backend.
    Note that this still works if the symlinks are dangling.

    If a symlink cannot be converted into an upload link, it will
    be used as a regular upload, i.e., the contents of the symlink
    destination will be uploaded by `start_upload`.
    In this case, an error will be raised if the symlink is dangling
    as there is no file that can actually be uploaded.
    If `links="always"`, an error is raised instead upon symlink
    conversion failure.

    This function is intended to be used with `clone_version`,
    which creates symlinks to files in `cache`.

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

    cache_dir = _cache_directory(cache_dir)

    out_files = []

    out_links = {
        "from_path": [],
        "to_project": [],
        "to_asset": [],
        "to_version": [],
        "to_path": [],
    }

    cache_dir = _normalize_and_sanitize_path(cache_dir)
    if not cache_dir.endswith("/"):
        cache_dir += "/"

    for root, _, files in os.walk(directory):
        for name in files:
            rel_path = os.path.relpath(os.path.join(root, name), directory)
            dest = (
                os.readlink(os.path.join(directory, rel_path))
                if os.path.islink(os.path.join(directory, rel_path))
                else None
            )
            if not dest:
                out_files.append(rel_path)
                continue

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
                out_links["from_path"].append(rel_path)
                out_links["to_project"].append(dest_components["project"])
                out_links["to_asset"].append(dest_components["asset"])
                out_links["to_version"].append(dest_components["version"])
                out_links["to_path"].append(dest_components["path"])
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
