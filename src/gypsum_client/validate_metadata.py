import json
from typing import Optional, Union

from jsonschema import validate as json_validate

__author__ = "Jayaram Kancherla"
__copyright__ = "Jayaram Kancherla"
__license__ = "MIT"


def validate_metadata(
    metadata: Union[str, dict], schema: str, stringify: Optional[bool] = None
) -> bool:
    """Validate metadata against a JSON schema for a SQLite database.

    See Also:
        :py:func:`~gypsum_client.fetch_metadata_schema.fetch_metadata_schema`, to get
        the JSON schema.

        :py:func:`~gypsum_client.fetch_metadata_database.fetch_metadata_database`,
        to obtain the SQLite database of metadata.

    Example:

        .. code-block:: python

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
            validate_metadata(metadata, schema)

    Args:
        metadata:
            Metadata to be checked.

            Usually a dictionary, but may also be a JSON-formatted string.

        schema:
            Path to a schema.

        stringify:
            Whether to convert ``metadata`` to a JSON-formatted string.
            Defaults to True if ``metadata`` is not already a string.

    Returns:
        True if metadata conforms to schema.
    """
    if stringify is None:
        stringify = not isinstance(metadata, str)

    if stringify:
        metadata = json.dumps(metadata)

    with open(schema) as f:
        schema_data = json.load(f)

    try:
        json_validate(instance=json.loads(metadata), schema=schema_data)
    except Exception as e:
        raise ValueError(f"Metadata validation failed: {e}") from e

    return True
