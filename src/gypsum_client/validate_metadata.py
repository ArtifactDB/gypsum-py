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
        raise ValueError(f"Metadata validation failed: {e}")

    return True
