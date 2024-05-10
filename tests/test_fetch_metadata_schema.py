import json
import tempfile

import pytest
from gypsum_client.fetch_metadata_schema import fetch_metadata_schema
from gypsum_client.validate_metadata import validate_metadata

__author__ = "Jayaram Kancherla"
__copyright__ = "Jayaram Kancherla"
__license__ = "MIT"


def test_fetchMetadataSchema():
    _cache_dir = tempfile.mkdtemp()
    path = fetch_metadata_schema(cache_dir=_cache_dir)
    assert isinstance(json.load(open(path)), dict)

    # Uses the cache
    with open(path, "w") as f:
        f.write("FOO_BAR")

    with pytest.raises(Exception):
        json.load(open(path))

    path2 = fetch_metadata_schema(cache_dir=_cache_dir)
    assert path == path2
    assert open(path).read().strip() == "FOO_BAR"

    # Unless we overwrite it
    man = fetch_metadata_schema(cache_dir=_cache_dir, overwrite=True)
    assert isinstance(json.load(open(path)), dict)


def test_validateMetadata():

    _cache_dir = tempfile.mkdtemp()

    metadata = {
        "title": "Fatherhood",
        "description": "Luke ich bin dein Vater.",
        "sources": [{"provider": "GEO", "id": "GSE12345"}],
        "taxonomy_id": ["9606"],
        "genome": ["GRCm38"],
        "maintainer_name": "Darth Vader",
        "maintainer_email": "vader@empire.gov",
        "bioconductor_version": "3.10",
    }

    schema = fetch_metadata_schema(cache_dir=_cache_dir)
    assert validate_metadata(metadata, schema)

    assert validate_metadata(json.dumps(metadata), schema)

    metadata.pop("bioconductor_version", None)
    with pytest.raises(Exception):
        validate_metadata(metadata, schema)
