import os

from ._utils import (
    BUCKET_CACHE_NAME,
    _cast_datetime,
    _fetch_cacheable_json,
    _fetch_json,
)
from .cache_directory import cache_directory
from .rest_url import rest_url

__author__ = "Jayaram Kancherla"
__copyright__ = "Jayaram Kancherla"
__license__ = "MIT"


def fetch_latest(project: str, asset: str, url: str = rest_url()) -> str:
    """Fetch the latest version of a project's asset.

    See Also:
        :py:func:`~gypsum_client.refresh_operations.refresh_latest`,
        to refresh the latest version.

    Example:

        .. code-block:: python

            ver = fetch_latest("test-R", "basic")

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
    project: str,
    asset: str,
    version: str,
    cache_dir: str = cache_directory(),
    overwrite: bool = False,
    url: str = rest_url(),
) -> dict:
    """Fetch the manifest for a version of an asset of a project.

    Example:

        .. code-block:: python

            manifest = fetch_manifest("test-R", "basic", "v1")

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
        Dictionary containing the manifest for this version.
        Each element is named after the relative path of a file in this version.
        The value of each element is another list with the following fields:
        - ``size``, an integer specifying the size of the file in bytes.
        - ``md5sum``, a string containing the hex-encoded MD5 checksum of the file.
        - Optional ``link``,  a list specifying the link destination for a file.

        This contains the strings ``project``, ``asset``, ``version`` and ``path``.
        If the link destination is itself a link, an ``ancestor`` list will be
        present that specifies the final location of the file after resolving all intermediate links.
    """
    return _fetch_cacheable_json(
        project,
        asset,
        version,
        "..manifest",
        url=url,
        cache=cache_dir,
        overwrite=overwrite,
    )


def fetch_permissions(project: str, url: str = rest_url()) -> dict:
    """Fetch the permissions for a project.

    See Also:
        :py:func:`~gypsum_client.set_operations.set_permissions`,
        to update or modify the permissions.

    Example:

        .. code-block:: python

            perms = fetch_permissions("test-R")

    Args:
        project:
            Project name.

        url:
            URL to the gypsum compatible API.

    Returns:
        Dictionary containing the permissions for this project:
        - ``owners``, a character vector containing the GitHub users or
        organizations that are owners of this project.
        - ``uploaders``, a list of lists specifying the users or organizations
        who are authorzied to upload to this project.

        Each entry is a list with the following fields:
        - ``id``, a string containing the GitHub user or organization
        that is authorized to upload.
        - Optional ``asset``, a string containing the name of the asset
        that the uploader is allowed to upload to. If not provided, there is no
        restriction on the uploaded asset name.
        - Optional ``version``, a string containing the name of the version
        that the uploader is allowed to upload to.If not provided, there is
        no restriction on the uploaded version name.
        - Optional ``until``a POSIXct object containing the expiry date of this
        authorization. If not provided, the authorization does not expire.
        - Optional ``trusted``, whether the uploader is trusted.
        If not provided, defaults to False.

    """
    perms = _fetch_json(f"{project}/..permissions", url=url)

    for i, val in enumerate(perms["uploaders"]):
        if "until" in val:
            perms["uploaders"][i]["until"] = _cast_datetime(val["until"])

    return perms


def fetch_quota(project: str, url: str = rest_url()) -> dict:
    """Fetch the quota details for a project.

    See Also:
        :py:func:`~gypsum_client.set_operations.set_quota`,
        to update or modify the quota.

    Example:

        .. code-block:: python

            quota = fetch_quota("test-R")

    Args:
        project:
            Project name.

        url:
            URL to the gypsum compatible API.

    Returns:
        Dictionary containing ``baseline``, the baseline quota at time zero in bytes;
        ``growth_rate``, the annual growth rate for the quota in bytes;
        ``year``, the creation year (i.e., time zero) for this project.
    """
    return _fetch_json(f"{project}/..quota", url=url)


def fetch_summary(
    project: str,
    asset: str,
    version: str,
    cache_dir: str = cache_directory(),
    overwrite: bool = False,
    url: str = rest_url(),
) -> dict:
    """Fetch the summary for a version of an asset of a project.

    Example:

        .. code-block:: python

            summa = fetch_summary("test-R", "basic", "v1")

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
        Dictionary containing the summary for this version, with the following fields:
        - ``upload_user_id``, string containing the identity of the uploader.
        - ``upload_start``, a POSIXct object containing the upload start time.
        - ``upload_finish``, a POSIXct object containing the upload finish time.
        - ``on_probation`` (optional), a logical scalar indicating whether the upload is probational.
            If missing, this can be assumed to be False.
    """
    _out = _fetch_cacheable_json(
        project,
        asset,
        version,
        "..summary",
        cache=cache_dir,
        overwrite=overwrite,
        url=url,
    )

    _out["upload_start"] = _cast_datetime(_out["upload_start"])
    _out["upload_finish"] = _cast_datetime(_out["upload_finish"])

    if "on_probation" in _out:
        if _out["on_probation"] is True and cache_dir is not None:
            _out_path = os.path.join(
                cache_dir, BUCKET_CACHE_NAME, project, asset, version, "..summary"
            )
            os.unlink(_out_path)

    return _out


def fetch_usage(project: str, url: str = rest_url()) -> int:
    """Fetch the quota usage for a project.

    See Also:
        :py:func:`~gypsum_client.refresh_operations.refresh_usage`,
        to refresh usage details.

    Example:

        .. code-block:: python

            usage = fetch_usage("test-R")

    Args:
        project:
            Project name.

        url:
            URL to the gypsum compatible API.

    Returns:
        Quota usage for the project, in bytes.
    """
    _usage = _fetch_json(f"{project}/..usage", url=url)
    return _usage["total"]
