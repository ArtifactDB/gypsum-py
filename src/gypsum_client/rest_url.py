from typing import Optional

__author__ = "Jayaram Kancherla"
__copyright__ = "Jayaram Kancherla"
__license__ = "MIT"

CURRENT_REST_URL = "https://gypsum.artifactdb.com"


def rest_url(url: Optional[str] = None):
    """URL for the gypsum REST API.

    Get or set the URL for the gypsum REST API.

    Args:
        url:
            URL to the gypsum REST API.
            Defaults to None.

    Returns:
        String containing the URL to the gypsum REST API.
    """
    global CURRENT_REST_URL
    if url is not None:
        CURRENT_REST_URL = url

    return CURRENT_REST_URL
