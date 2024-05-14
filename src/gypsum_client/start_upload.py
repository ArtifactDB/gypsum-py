import hashlib
import os
from typing import List, Union
from urllib.parse import quote_plus

import requests

from ._utils import _remove_slash_url, _rest_url, _sanitize_path
from .auth import access_token
from .config import REQUESTS_MOD

__author__ = "Jayaram Kancherla"
__copyright__ = "Jayaram Kancherla"
__license__ = "MIT"


def start_upload(
    project: str,
    asset: str,
    version: str,
    files: Union[str, List[str]],
    links: Union[str, List[str]] = None,
    deduplicate: bool = True,
    probation: bool = False,
    url: str = _rest_url(),
    token: str = access_token(),
    directory: str = None,
):
    """Start an upload.

    Start an upload of a new version of an asset,
    or a new asset of a project.

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

    _targets = []
    if directory is not None:
        for f in files:
            _targets.append(os.path.join(directory, f))

    files = []
    for _tg in _targets:
        file_info = {
            "path": _tg,
            "size": os.path.getsize(_tg),
            "md5sum": hashlib.md5(open(_tg, "rb").read()).hexdigest(),
            "dedup": deduplicate,
        }
        files.append(file_info)

    formatted = []
    for _, file in enumerate(files):
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

    url = _remove_slash_url(url)
    req = requests.post(
        f"{url}/upload/start/{quote_plus(project)}/{quote_plus(asset)}/{quote_plus(version)}",
        json={"files": formatted, "on_probation": probation},
        headers={"Authorization": f"Bearer {token}"},
        verify=REQUESTS_MOD["verify"],
    )
    req.raise_for_status()

    return req.json()
