"""
Set this to False if SSL certificates are not properly setup on your machine.

essentially sets ``verify=False`` on all requests to the gypsum REST API.

Example:

    .. code-block::python

        from gypsum_client import REQUESTS_MOD
        # to set verify to False
        REQUESTS_MOD["verify"] = False

"""

__author__ = "Jayaram Kancherla"
__copyright__ = "Jayaram Kancherla"
__license__ = "MIT"

REQUESTS_MOD = {"verify": True}
