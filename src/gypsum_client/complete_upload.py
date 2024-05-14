import requests

from ._utils import _remove_slash_url, _rest_url

__author__ = "Jayaram Kancherla"
__copyright__ = "Jayaram Kancherla"
__license__ = "MIT"


def complete_upload(init: dict, url=_rest_url()) -> dict:
    """Complete an upload session after all files have been uploaded.

    Args:
        init:
            Dictionary containing ``complete_url`` and ``session_token``.

        url:
            URL to the gypsum REST API.

    Returns:
        True after completion.
    """
    url = _remove_slash_url(url)
    req = requests.post(
        f"{url}{init['complete_url']}",
        headers={"Authorization": f"Bearer {init['session_token']}"},
    )
    req.raise_for_status()

    return True
