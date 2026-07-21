"""DSMS Semantics Module

Exposes :func:`schema_to_oold`, used by :meth:`KItem.populate_schema` to
convert simplified input dicts to OO-LD documents via the semantic schema
transforms defined in the k-type spec.
"""

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


def schema_to_oold(
    schema_url: str, input_data: Dict[str, Any]
) -> Dict[str, Any]:
    """Convert a simplified input dict to an OO-LD document.

    Loads the schema identified by *schema_url* using
    :meth:`semantic_schemas.Schema.from_url`, then applies its
    ``transform.simplified.jsonata`` transform to *input_data*.

    If the schema has no simplified transform, *input_data* is returned as-is
    (the caller is expected to pass OO-LD directly in that case).

    Args:
        schema_url: A GitHub tree URL pointing to the schema folder, as stored
            in the k-type spec's ``semantic_schemas[].url`` field.
        input_data: Simplified input dict (for schemas with a transform) or an
            OO-LD dict (for schemas without a transform).

    Returns:
        OO-LD document dict ready to be stored as ``KItemSchemaData.content``.

    Raises:
        ImportError: If the ``semantic-schemas`` package is not installed.
        RuntimeError: If the schema YAML cannot be fetched.
    """
    try:
        from semantic_schemas import Schema
    except ImportError as exc:
        raise ImportError(
            "The 'semantic-schemas' package is required to apply simplified "
            "input transforms. Install it with: pip install semantic-schemas"
        ) from exc

    schema = Schema.from_url(schema_url)

    if schema._transform_src is None:  # pylint: disable=protected-access
        logger.debug(
            "No simplified transform found at %s — treating input as OO-LD",
            schema_url,
        )
        return input_data

    return schema.transform(input_data)
