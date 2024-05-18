import requests

from ._utils import _remove_slash_url, _rest_url

__author__ = "Jayaram Kancherla"
__copyright__ = "Jayaram Kancherla"
__license__ = "MIT"


def abort_upload(init: dict, url=_rest_url()) -> dict:
    """Abort an upload session, usually after an irrecoverable error.

    Args:
        init:
            Dictionary containing ``abort_url`` and ``session_token``.

        url:
            URL to the gypsum REST API.

    Returns:
        True after completion.
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
        )

    return True
