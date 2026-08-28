"""DSMS Semantics Module

Exposes :func:`schema_to_oold`, used by :meth:`KItem.populate_schema` to
convert simplified input dicts to OO-LD documents via the semantic schema
transforms defined in the k-type spec.
"""

import logging
from typing import Any, Dict

import requests

logger = logging.getLogger(__name__)


def schema_to_oold(
    schema_url: str, input_data: Dict[str, Any]
) -> Dict[str, Any]:
    """Convert a simplified input dict to an OO-LD document.

    Fetches ``specs/transform.simplified.jsonata`` from *schema_url* (a raw
    GitHub base URL) and applies the JSONata transform to *input_data*.  If
    the transform file does not exist (HTTP 404), *input_data* is returned
    as-is — the caller is expected to pass OO-LD directly in that case.

    Args:
        schema_url: Raw GitHub URL pointing to the schema folder, as stored
            in the k-type spec's ``semantic_schemas[].url`` field.
        input_data: Simplified input dict (for schemas with a transform) or an
            OO-LD dict (for schemas without a transform).

    Returns:
        OO-LD document dict ready to be stored as ``KItemSchemaData.content``.

    Raises:
        ImportError: If the ``semantic-schemas`` package is not installed.
        requests.HTTPError: If fetching the transform file fails (non-404).
    """
    try:
        from jsonata.jsonata import Jsonata
    except ImportError as exc:
        raise ImportError(
            "The 'semantic-schemas' package is required to apply simplified "
            "input transforms. Install it with: pip install semantic-schemas"
        ) from exc

    transform_url = (
        f"{schema_url.rstrip('/')}/specs/transform.simplified.jsonata"
    )
    response = requests.get(transform_url, timeout=30)

    if response.status_code == 404:
        logger.debug(
            "No simplified transform found at %s — treating input as OO-LD",
            schema_url,
        )
        return input_data

    response.raise_for_status()
    return Jsonata(response.text).evaluate(input_data)
