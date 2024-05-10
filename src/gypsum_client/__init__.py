import sys

if sys.version_info[:2] >= (3, 8):
    # TODO: Import directly (no need for conditional) when `python_requires = >= 3.8`
    from importlib.metadata import PackageNotFoundError, version  # pragma: no cover
else:
    from importlib_metadata import PackageNotFoundError, version  # pragma: no cover

try:
    # Change here if project is renamed and does not equal the package name
    dist_name = "gypsum-client"
    __version__ = version(dist_name)
except PackageNotFoundError:  # pragma: no cover
    __version__ = "unknown"
finally:
    del version, PackageNotFoundError

from .auth import access_token, set_access_token
from .fetch_assets import (
    fetch_latest,
    fetch_manifest,
    fetch_permissions,
    fetch_quota,
    fetch_summary,
    fetch_usage,
)
from .fetch_metadata_database import fetch_metadata_database
from .fetch_metadata_schema import fetch_metadata_schema
from .list_assets import list_assets, list_files, list_projects, list_versions
from .s3_config import public_s3_config
