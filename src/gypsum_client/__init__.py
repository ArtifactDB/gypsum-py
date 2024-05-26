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


from ._utils import BUCKET_CACHE_NAME
from .auth import access_token, set_access_token
from .cache_directory import cache_directory
from .clone_operations import clone_version
from .config import REQUESTS_MOD
from .create_operations import create_project
from .fetch_metadata_database import fetch_metadata_database
from .fetch_metadata_schema import fetch_metadata_schema
from .fetch_operations import (
    fetch_latest,
    fetch_manifest,
    fetch_permissions,
    fetch_quota,
    fetch_summary,
    fetch_usage,
)
from .list_operations import list_assets, list_files, list_projects, list_versions
from .prepare_directory_for_upload import prepare_directory_upload
from .probation_operations import approve_probation, reject_probation
from .refresh_operations import refresh_latest, refresh_usage
from .remove_operations import remove_asset, remove_project, remove_version
from .resolve_links import resolve_links
from .rest_url import rest_url
from .s3_config import public_s3_config
from .save_operations import save_file, save_version
from .search_metadata import define_text_query, search_metadata_text
from .set_operations import set_permissions, set_quota
from .upload_api_operations import abort_upload, complete_upload, start_upload
from .upload_file_actions import upload_directory, upload_files
from .validate_metadata import validate_metadata
