import hashlib
import os
from typing import List, Union
from urllib.parse import quote_plus

import requests

from ._utils import _remove_slash_url, _sanitize_path
from .auth import access_token
from .config import REQUESTS_MOD
from .rest_url import rest_url

__author__ = "Jayaram Kancherla"
__copyright__ = "Jayaram Kancherla"
__license__ = "MIT"


def start_upload(
    project: str,
    asset: str,
    version: str,
    files: Union[str, List[str], List[dict]],
    links: List[dict] = None,
    deduplicate: bool = True,
    probation: bool = False,
    url: str = rest_url(),
    token: str = None,
    directory: str = None,
) -> dict:
    """Start an upload.

    Start an upload of a new version of an asset,
    or a new asset of a project.

    See Also:
        :py:func:`~gypsum_client.upload_file_operations.upload_files`,
        to actually upload the files.

        :py:func:`~.complete_upload`,
        to indicate that the upload is completed.

        :py:func:`~.abort_upload`,
        to abort an upload in progress.

        :py:func:`~gypsum_client.prepare_directory_for_upload.prepare_directory_upload`,
        to create ``files`` and ``links`` from a directory.

    Example:

        .. code-block:: python

            import tempfile
            tmp_dir = tempfile.mkdtemp()

            with open(f"{tmp_dir}/blah.txt", "w") as f:
                f.write(blah_contents)

            os.makedirs(f"{tmp_dir}/foo", exist_ok=True)

            with open(f"{tmp_dir}/foo/blah.txt", "w") as f:
                f.write(foobar_contents)

            files = [
                str(file.relative_to(tmp_dir))
                for file in Path(tmp_dir).rglob("*")
                if not os.path.isdir(file)
            ]

            init = start_upload(
                project="test-Py-demo",
                asset="upload",
                version="1",
                files=files,
                directory=tmp_dir,
            )

            abort_upload(init)

    Args:
        project:
            Project name.

        asset:
            Asset name.

        version:
            Version name.

        files:
            A file path or a List of file paths to upload.
            These paths are assumed to be relative to the
            ``directory`` parameter.

            Optionally, May be provided a list where each element
            is a dictionary containing the following keys:
            - ``path``: a string containing the relative path of the
            file inside the version's subdirectory.
            - ``size``, a non-negative integer specifying the size of the
            file in bytes.
            - ``md5sum``, a string containing the hex-encoded MD5
            checksum of the file.
            - Optionally ``dedup``, a boolean value indicating
            whether deduplication should be attempted for each file. If this is
            not available, the parameter ``deduplicate`` is used.


        links:
            A List containing a dictionary with the following keys:
            - ``from.path``: a string containing the relative path of the
            file inside the version's subdirectory.
            - ``to.project``: a string containing the project of the list
            destination.
            - ``to.asset``: a string containing the asset of the list
            destination.
            - ``to.version``: a string containing the version of the list
            destination.
            - ``to.path``: a string containing the path of the list destination.

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

        directory:
            Path to a directory containing the ``files`` to be uploaded.
            This directory is assumed to correspond to a version of an asset.

    Returns:
        Dictionary containing the following keys:
        - ``file_urls``, a list of lists containing information about each
        file to be uploaded. This is used by ``uploadFiles``.
        - ``complete_url``, a string containing the completion URL, to be
        used by ``complete_upload``.
        - ``abort_url``, a string specifying the abort URL, to be used by
        ``abort_upload``.
        - ``session_token``, a string for authenticating to the newly
        initialized upload session.
    """
    if isinstance(files, str):
        files = [files]

    _types_in_file = [type(f) for f in files]

    if len(set(_types_in_file)) > 1:
        raise ValueError(
            "All elements in 'files' must be strings or dicts, but not a mix."
        )

    _all_dict_in_files = all(isinstance(f, dict) for f in files)
    if _all_dict_in_files is False:
        _targets = []
        for f in files:
            if directory is not None:
                _targets.append(os.path.join(directory, f))
            else:
                _targets.append(f)

        _files_info = []
        for _tidx, _tg in enumerate(_targets):
            file_info = {
                "path": files[_tidx],
                "size": os.path.getsize(_tg),
                "md5sum": hashlib.md5(open(_tg, "rb").read()).hexdigest(),
                "dedup": deduplicate,
            }
            _files_info.append(file_info)
    else:
        _files_info = []
        for f in files:
            file_info = {
                "path": f["path"],
                "size": f["size"],
                "md5sum": f["md5sum"],
                "dedup": f["dedup"] if "dedup" in f else deduplicate,
            }
            _files_info.append(file_info)

    formatted = []
    for _, file in enumerate(_files_info):
        file_type = "simple" if file["dedup"] else "dedup"
        formatted.append(
            {
                "type": file_type,
                "path": _sanitize_path(file["path"]),
                "size": file["size"],
                "md5sum": file["md5sum"],
            }
        )

    if links is not None:
        out_links = []
        for _, link in enumerate(links):
            out_links.append(
                {
                    "type": "link",
                    "path": _sanitize_path(link["from.path"]),
                    "link": {
                        "project": link["to.project"],
                        "asset": link["to.asset"],
                        "version": link["to.version"],
                        "path": _sanitize_path(link["to.path"]),
                    },
                }
            )
        formatted.extend(out_links)

    if token is None:
        token = access_token()

    url = _remove_slash_url(url)
    req = requests.post(
        f"{url}/upload/start/{quote_plus(project)}/{quote_plus(asset)}/{quote_plus(version)}",
        json={"files": formatted, "on_probation": probation},
        headers={"Authorization": f"Bearer {token}"},
        verify=REQUESTS_MOD["verify"],
    )
    try:
        req.raise_for_status()
    except Exception as e:
        raise Exception(
            f"Failed to start an upload, {req.status_code} and reason: {req.text}"
        ) from e

    resp = req.json()

    if "status" in resp and resp["status"] == "error":
        raise Exception(
            f"Failed to upload, {req.status_code} and reason: {resp['reason']}"
        )

    return resp


def complete_upload(init: dict, url=rest_url()):
    """Complete an upload session after all files have been uploaded.

    See Also:
        :py:func:`~gypsum_client.upload_api_operations.start_upload`,
        to create the init.

    Example:

        .. code-block:: python

            import tempfile
            tmp_dir = tempfile.mkdtemp()

            with open(f"{tmp_dir}/blah.txt", "w") as f:
                f.write(blah_contents)

            os.makedirs(f"{tmp_dir}/foo", exist_ok=True)

            with open(f"{tmp_dir}/foo/blah.txt", "w") as f:
                f.write(foobar_contents)

            files = [
                str(file.relative_to(tmp_dir))
                for file in Path(tmp_dir).rglob("*")
                if not os.path.isdir(file)
            ]

            init = start_upload(
                project="test-Py-demo",
                asset="upload",
                version="1",
                files=files,
                directory=tmp_dir,
            )

            abort_upload(init)

    Args:
        init:
            Dictionary containing ``complete_url`` and ``session_token``.

            :py:func:`~.start_upload`, to create ``init``.

        url:
            URL to the gypsum REST API.
    """
    url = _remove_slash_url(url)
    req = requests.post(
        f"{url}{init['complete_url']}",
        headers={"Authorization": f"Bearer {init['session_token']}"},
    )
    try:
        req.raise_for_status()
    except Exception as e:
        raise Exception(
            f"Failed to complete an upload session, {req.status_code} and reason: {req.text}"
        ) from e


def abort_upload(init: dict, url=rest_url()):
    """Abort an upload session, usually after an irrecoverable error.

    See Also:
        :py:func:`~gypsum_client.upload_api_operations.start_upload`,
        to create the init.

    Example:

        .. code-block:: python

            import tempfile
            tmp_dir = tempfile.mkdtemp()

            with open(f"{tmp_dir}/blah.txt", "w") as f:
                f.write(blah_contents)

            os.makedirs(f"{tmp_dir}/foo", exist_ok=True)

            with open(f"{tmp_dir}/foo/blah.txt", "w") as f:
                f.write(foobar_contents)

            files = [
                str(file.relative_to(tmp_dir))
                for file in Path(tmp_dir).rglob("*")
                if not os.path.isdir(file)
            ]

            init = start_upload(
                project="test-Py-demo",
                asset="upload",
                version="1",
                files=files,
                directory=tmp_dir,
            )

            complete_upload(init)

    Args:
        init:
            Dictionary containing ``abort_url`` and ``session_token``.

            :py:func:`~.start_upload`, to create ``init``.

        url:
            URL to the gypsum REST API.
    """
    url = _remove_slash_url(url)
    req = requests.post(
        f"{url}{init['abort_url']}",
        headers={"Authorization": f"Bearer {init['session_token']}"},
    )

    try:
        req.raise_for_status()
    except Exception as e:
        raise Exception(
            f"Failed to abort the upload, {req.status_code} and reason: {req.text}"
        ) from e
