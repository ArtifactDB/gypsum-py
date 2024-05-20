import os
from multiprocessing import Pool

import requests

from ._utils import _remove_slash_url
from .auth import access_token
from .cache_directory import cache_directory
from .config import REQUESTS_MOD
from .prepare_directory_for_upload import prepare_directory_upload
from .rest_url import rest_url
from .upload_api_operations import abort_upload, complete_upload, start_upload

__author__ = "Jayaram Kancherla"
__copyright__ = "Jayaram Kancherla"
__license__ = "MIT"


def upload_directory(
    directory: str,
    project: str,
    asset: str,
    version: str,
    cache_dir: str = cache_directory(),
    deduplicate: bool = True,
    probation: bool = False,
    url: str = rest_url(),
    token: str = None,
    concurrent: int = 1,
    abort_failed: bool = True,
) -> bool:
    """Upload a directory to the gypsum backend.

    This function is a wrapper around
    :py:func:`~gypsum_client.prepare_directory_for_upload.prepare_directory_upload`
    and :py:func:`~gypsum_client.upload_api_operations.start_upload` and others.

    The aim is to streamline the upload of a directory's contents
    when no customization of the file listing is required.

    Convenience method to upload a directory to the gypsum backend
    as a versioned asset of a project. This requires uploader permissions
    to the relevant project.

    Example:

        .. code-block:: python

            tmp_dir = tempfile.mkdtemp()

            with open(os.path.join(tmp, "blah.txt"), "w") as f:
                f.write("ABCDEFGHIJKLMNOPQRSTUVWXYZ")

            os.makedirs(os.path.join(tmp, "foo"))
            with open(os.path.join(tmp, "foo", "bar.txt"), "w") as f:
                f.write("\n".join(map(str, range(1, 11))))

            upload_directory(
                tmp, "test-Py",
                "upload-dir", version="1"
            )

    Args:
        directory:
            Path to a directory containing the ``files`` to be uploaded.
            This directory is assumed to correspond to a version of an asset.

        project:
            Project name.

        asset:
            Asset name.

        version:
            Version name.

        cache_dir:
            Path to the cache for saving files, e.g., in
            :py:func:`~gypsum_client.save_operations.save_version`.

            Used to convert symbolic links to upload links,see
            :py:func:`~gypsum_client.prepare_directory_for_upload.prepare_directory_upload`.

        deduplicate:
            Whether the backend should attempt deduplication of ``files``
            in the immediately previous version.
            Defaults to True.

        probation:
            Whether to perform a probational upload.
            Defaults to False.

        url:
            URL of the gypsum REST API.

        token:
            GitHub access token to authenticate to the gypsum REST API.

        concurrent:
            Number of concurrent downloads.
            Defaults to 1.

        abort_failed:
            Whether to abort the upload on any failure.

            Setting this to `False` can be helpful for diagnosing upload problems.

    Returns:
        `True` if successfull, otherwise `False`.
    """

    if token is None:
        token = access_token()

    listing = prepare_directory_upload(directory, links="always", cache_dir=cache_dir)

    blob = start_upload(
        project=project,
        asset=asset,
        version=version,
        files=listing["files"],
        links=listing["links"],
        directory=directory,
        probation=probation,
        url=url,
        token=token,
    )

    success = False
    try:
        upload_files(blob, directory=directory, url=url, concurrent=concurrent)
        complete_upload(blob, url=url)
        success = True
    finally:
        if abort_failed and not success:
            abort_upload(blob)

    return success


def _upload_file_wrapper(args):
    file_info, directory, url, session_token = args
    _upload_file(file_info, directory, url, session_token)


def upload_files(
    init: dict, directory: str = None, url: str = rest_url(), concurrent: int = 1
):
    """Upload files in an initialized upload session for a version of an asset.

    Args:
        init:
            Dictionary containing ``file_urls`` and ``session_token``.
            This is typically the return value from
            :py:func:`~gypsum_client.start_upload.start_upload``.

        directory:
            Path to the directory containing files.
            Defaults to None, if files are part of the current working directory.

        url:
            URL of the gypsum REST API.

        concurrent:
            Number of concurrent uploads.
            Defaults to 1.
    """
    url = _remove_slash_url(url)

    if concurrent <= 1:
        for file_info in init["file_urls"]:
            _upload_file(file_info, directory, url, init["session_token"])
    else:
        with Pool(concurrent) as pool:
            _args = [
                (file_info, directory, url, init["session_token"])
                for file_info in init["file_urls"]
            ]
            pool.map(_upload_file_wrapper, _args)


def _upload_file(info: dict, directory: str, url: str, token: str):
    _path = info["path"]

    if directory is not None:
        _path = os.path.join(directory, _path)

    if info["method"] == "presigned":
        req_url = f"{url}{info['url']}"
        headers = {"Authorization": f"Bearer {token}"}
        res = requests.post(req_url, headers=headers, verify=REQUESTS_MOD["verify"])
        try:
            res.raise_for_status()
        except Exception as e:
            raise Exception(
                f"Failed to fetch pre-signed url, {res.status_code} and reason: {res.text}"
            ) from e

        presigned = res.json()

        req2_url = presigned["url"]
        headers2 = {"Content-MD5": presigned["md5sum_base64"]}
        with open(_path, "rb") as f:
            res2 = requests.put(
                req2_url, headers=headers2, data=f, verify=REQUESTS_MOD["verify"]
            )
            try:
                res2.raise_for_status()
            except Exception as e:
                raise Exception(
                    f"Failed to upload assets in the project, {res2.status_code} and reason: {res2.text}"
                ) from e
    else:
        raise ValueError(
            f"unknown upload method '{info['method']}' for file '{info['path']}'"
        )
