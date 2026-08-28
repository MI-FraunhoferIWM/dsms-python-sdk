"""DSMS Semantics Module

Provides :func:`schema_to_webform` — the primary entry point used by
:meth:`KItem.populate_schema` to convert simplified input dicts into the
DSMS frontend webform format (``{sections: [{entries: [...]}]}``) via an
OO-LD schema definition.

Also retains :func:`schema_to_oold` for callers that need the raw OO-LD
ontology dict produced by the JSONata transform.
"""

import logging
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import requests

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# URL helpers
# ---------------------------------------------------------------------------


def _to_raw_url(url: str) -> str:
    """Convert a GitHub blob URL to a raw.githubusercontent.com URL (no-op otherwise)."""
    if "github.com" in url and "/blob/" in url:
        url = url.replace("github.com", "raw.githubusercontent.com")
        url = url.replace("/blob/", "/")
    return url


def _to_raw_specs_url(url: str) -> str:
    """Normalise a schema URL to the raw-content ``specs/`` folder URL.

    Strips the trailing filename (e.g. ``schema.oold.yaml``) and ensures the
    result ends with ``/specs``.  GitHub blob URLs are converted to raw URLs.

    Examples::

        https://github.com/org/repo/blob/ref/.../TTO/specs/schema.oold.yaml
        → https://raw.githubusercontent.com/org/repo/ref/.../TTO/specs
    """
    if "github.com" in url and "/blob/" in url:
        url = url.replace("github.com", "raw.githubusercontent.com")
        url = url.replace("/blob/", "/")

    url = url.rstrip("/")

    # Strip a trailing filename (any component containing a dot)
    parts = url.rsplit("/", 1)
    if len(parts) == 2 and "." in parts[-1]:
        url = parts[0]

    if not url.endswith("/specs"):
        url = f"{url}/specs"

    return url


# ---------------------------------------------------------------------------
# IRI / @context helpers
# ---------------------------------------------------------------------------


def _build_prefixes(context: Dict[str, Any]) -> Dict[str, str]:
    """Build a prefix → base-IRI map from a JSON-LD @context."""
    prefixes: Dict[str, str] = {}
    for key, value in context.items():
        if key.startswith("@") or key in ("type", "id"):
            continue
        if isinstance(value, str):
            prefixes[key] = value
        elif (
            isinstance(value, dict)
            and value.get("@prefix") is True
            and isinstance(value.get("@id"), str)
        ):
            prefixes[key] = value["@id"]
    return prefixes


def _expand_iri(iri: str, prefixes: Dict[str, str]) -> str:
    """Expand a prefixed IRI (e.g. ``rdfs:label``) using *prefixes*."""
    if not iri:
        return iri
    if iri.startswith("http://") or iri.startswith("https://"):
        return iri
    colon = iri.find(":")
    if colon == -1:
        return iri
    prefix = iri[:colon]
    local = iri[colon + 1:]
    return prefixes.get(prefix, prefix + ":") + local


def _resolve_relation_mapping(
    prop_name: str, context: Dict[str, Any], prefixes: Dict[str, str]
) -> Optional[Dict[str, Any]]:
    """Build a ``relationMapping`` dict for *prop_name* from the @context."""
    entry = context.get(prop_name)
    if not entry:
        return None
    if isinstance(entry, str):
        return {
            "iri": _expand_iri(entry, prefixes),
            "type": "data_property",
            "label": prop_name,
            "inverse": False,
        }
    if isinstance(entry, dict) and "@id" in entry:
        iri = _expand_iri(entry["@id"], prefixes)
        prop_type = "object_property" if entry.get("@type") == "@id" else "data_property"
        return {"iri": iri, "type": prop_type, "label": prop_name, "inverse": False}
    return None


# ---------------------------------------------------------------------------
# Widget mapping (mirrors oold-adapter.ts mapProperty logic)
# ---------------------------------------------------------------------------


def _map_widget(prop_schema: Dict[str, Any]) -> str:
    """Return the DSMS widget type string for a JSON Schema property definition."""
    prop_type = prop_schema.get("type", "string")
    prop_format = prop_schema.get("format", "")

    if prop_type == "array" and prop_format == "kitem":
        return "Knowledge item"
    if prop_format == "kitem":
        return "Knowledge item"
    if prop_type == "boolean":
        return "Checkbox"
    if prop_format == "slider":
        return "Slider"
    if prop_type in ("number", "integer"):
        return "Number"
    if prop_format == "textarea":
        return "Textarea"
    if prop_format == "date":
        return "Date"
    if prop_format == "date-time":
        return "Date-time"
    if prop_format == "uri" and prop_schema.get("x-kitem"):
        return "Knowledge item"
    if prop_format == "uri":
        return "URL"
    if prop_type == "array" and prop_schema.get("items", {}).get("enum"):
        return "Multi-select"
    if prop_type == "array" and prop_schema.get("items", {}).get("format") == "uri":
        return "Knowledge item"
    if prop_schema.get("enum"):
        fmt = (prop_format or "").lower()
        if fmt == "star-rating":
            return "Star rating"
        if fmt == "radio":
            return "Radio"
        return "Select"
    if prop_type == "array" and prop_schema.get("x-vocabulary"):
        return "Multi-select"
    if prop_schema.get("x-vocabulary"):
        return "Select"
    if prop_format == "latex":
        return "LaTeX"
    return "Text"


# ---------------------------------------------------------------------------
# Value conversion: OO-LD ontology value → webform entry value
# ---------------------------------------------------------------------------


def _convert_scalar_value(prop_schema: Dict[str, Any], value: Any) -> Any:
    """Convert an OO-LD scalar/list value to the webform entry value format."""
    if value is None:
        return None

    widget = _map_widget(prop_schema)

    # Vocabulary / enum selects → {key, label, value} objects
    if widget in ("Select", "Multi-select", "Radio", "Star rating") or \
            prop_schema.get("x-vocabulary") or prop_schema.get("enum"):
        if isinstance(value, str):
            return {"key": value, "label": value, "value": value}
        if isinstance(value, list):
            return [
                {"key": v, "label": v, "value": v} if isinstance(v, str) else v
                for v in value
            ]

    # Knowledge item → [{id, ktype_id, slug, name}]
    if widget == "Knowledge item":
        if isinstance(value, list):
            return [
                {"id": v, "ktype_id": "", "slug": "", "name": ""}
                if isinstance(v, str) else v
                for v in value
            ]
        if isinstance(value, str):
            return [{"id": value, "ktype_id": "", "slug": "", "name": ""}]

    return value


# ---------------------------------------------------------------------------
# Array-group helpers: flatten OO-LD nested objects → flat row dicts
# ---------------------------------------------------------------------------


def _fill_flat_row(
    item_schema: Dict[str, Any],
    oold_item: Dict[str, Any],
    path_prefix: str,
    context: Dict[str, Any],
    prefixes: Dict[str, str],
) -> Dict[str, Any]:
    """Build a flat ``{key: value}`` row from an OO-LD object.

    Mirrors the TypeScript ``flattenObjectProps`` path-prefixing logic so that
    nested schema properties (e.g. ``has_value_spec.result_value``) become flat
    keys (``has_value_spec_result_value``) matching the stored webform format.
    """
    row: Dict[str, Any] = {}
    for prop_name, prop_schema in item_schema.get("properties", {}).items():
        if prop_schema.get("readOnly"):
            continue
        flat_key = f"{path_prefix}_{prop_name}" if path_prefix else prop_name
        value = oold_item.get(prop_name) if isinstance(oold_item, dict) else None

        if prop_schema.get("type") == "object":
            nested = value if isinstance(value, dict) else {}
            row.update(_fill_flat_row(prop_schema, nested, flat_key, context, prefixes))
        elif prop_schema.get("type") == "array" and prop_schema.get("items", {}).get("type") == "object":
            # Nested array-of-objects within an array item: too deep to flatten generically
            pass
        else:
            converted = _convert_scalar_value(prop_schema, value)
            if converted is not None:
                row[flat_key] = converted
    return row


def _build_array_group_entry(
    prop_name: str,
    prop_schema: Dict[str, Any],
    entry_id: str,
    context: Dict[str, Any],
    prefixes: Dict[str, str],
    oold_value: Any,
) -> Dict[str, Any]:
    """Build an ``Array group`` webform entry dict."""
    label = prop_schema.get("title", prop_name)
    item_schema = prop_schema.get("items", {})

    value_rows: List[Dict[str, Any]] = []
    if isinstance(oold_value, list):
        for oold_item in oold_value:
            if isinstance(oold_item, dict):
                row = _fill_flat_row(item_schema, oold_item, "", context, prefixes)
                if row:
                    value_rows.append(row)

    entry: Dict[str, Any] = {
        "id": entry_id,
        "label": label,
        "type": "Array group",
        "value": value_rows,
    }

    rm = _resolve_relation_mapping(prop_name, context, prefixes)
    if rm:
        entry["relationMapping"] = rm

    return entry


# ---------------------------------------------------------------------------
# Entry builders
# ---------------------------------------------------------------------------


def _make_scalar_entry(
    entry_id: str,
    prop_name: str,
    prop_schema: Dict[str, Any],
    context: Dict[str, Any],
    prefixes: Dict[str, str],
    value: Any,
) -> Optional[Dict[str, Any]]:
    """Build a single scalar/kitem/select webform entry dict."""
    if prop_schema.get("readOnly"):
        return None
    if prop_schema.get("type") == "object":
        return None
    if prop_schema.get("type") == "array" and prop_schema.get("items", {}).get("type") == "object":
        return None

    widget = _map_widget(prop_schema)
    label = prop_schema.get("title", prop_name)

    entry: Dict[str, Any] = {
        "id": entry_id,
        "label": label,
        "type": widget,
    }

    converted = _convert_scalar_value(prop_schema, value)
    if converted is not None:
        entry["value"] = converted

    rm = _resolve_relation_mapping(prop_name, context, prefixes)
    if rm:
        entry["relationMapping"] = rm

    return entry


def _flatten_object_to_entries(
    obj_schema: Dict[str, Any],
    path_prefix: str,
    context: Dict[str, Any],
    prefixes: Dict[str, str],
    oold_values: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """Flatten a nested object schema into webform entries (for doubly-nested objects)."""
    entries: List[Dict[str, Any]] = []
    for prop_name, prop_schema in obj_schema.get("properties", {}).items():
        entry_id = f"{path_prefix}_{prop_name}" if path_prefix else prop_name
        value = oold_values.get(prop_name) if isinstance(oold_values, dict) else None

        if prop_schema.get("readOnly"):
            continue
        if prop_schema.get("type") == "object":
            nested_values = value if isinstance(value, dict) else {}
            entries.extend(
                _flatten_object_to_entries(prop_schema, entry_id, context, prefixes, nested_values)
            )
        elif prop_schema.get("type") == "array" and prop_schema.get("items", {}).get("type") == "object":
            arr_entry = _build_array_group_entry(prop_name, prop_schema, entry_id, context, prefixes, value)
            entries.append(arr_entry)
        else:
            e = _make_scalar_entry(entry_id, prop_name, prop_schema, context, prefixes, value)
            if e:
                entries.append(e)
    return entries


# ---------------------------------------------------------------------------
# $ref / allOf resolution
# ---------------------------------------------------------------------------


def _resolve_schema_refs(
    schema: Dict[str, Any], schema_url: str
) -> Dict[str, Any]:
    """Recursively resolve ``allOf: [$ref: ...]`` entries by fetching and merging.

    Mirrors ``resolveSchemaRefs`` from ``oold-adapter.ts``:
    - Base schema @context/properties/required are merged first.
    - Extending schema overrides same-named properties.
    - Required arrays are unioned.
    """
    import yaml as _yaml

    if not schema.get("allOf"):
        return schema

    merged = {k: v for k, v in schema.items() if k != "allOf"}

    for entry in schema.get("allOf", []):
        ref = entry.get("$ref")
        if not ref:
            continue
        resolved_url = _to_raw_url(urljoin(schema_url, ref))
        logger.debug("Resolving $ref: %s", resolved_url)
        try:
            resp = requests.get(resolved_url, timeout=30)
            resp.raise_for_status()
            base = (
                _yaml.safe_load(resp.text)
                if resolved_url.endswith((".yaml", ".yml"))
                else __import__("json").loads(resp.text)
            )
        except Exception as exc:
            logger.warning("Failed to resolve $ref %s: %s", resolved_url, exc)
            continue

        base = _resolve_schema_refs(base, resolved_url)

        # Merge: base provides defaults, extending schema wins per-key
        merged["@context"] = {**base.get("@context", {}), **merged.get("@context", {})}
        merged["properties"] = {**base.get("properties", {}), **merged.get("properties", {})}
        merged["required"] = list(
            set(base.get("required", []) + merged.get("required", []))
        )

    return merged


# ---------------------------------------------------------------------------
# Core webform builder
# ---------------------------------------------------------------------------


def _parse_oold_schema_to_webform(
    schema: Dict[str, Any], oold_doc: Dict[str, Any]
) -> Dict[str, Any]:
    """Build the webform ``{sections: [{entries: [...]}]}`` dict.

    Mirrors ``parseOoldSchema`` from ``oold-adapter.ts``:
    - Top-level ``type:object`` properties → separate named sections.
    - Top-level ``type:array`` of objects → ``Array group`` in main section.
    - Everything else → scalar/kitem/select entry in main section (``oold_section_0``).
    - ``x-transformers`` → prepends a ``File`` entry to the first section.
    - All values are filled from *oold_doc* (the OO-LD transform output).

    Args:
        schema:   Resolved OO-LD schema dict (allOf/$ref already merged).
        oold_doc: OO-LD ontology dict produced by the JSONata transform, or
                  the raw simplified input if no transform exists.

    Returns:
        Webform dict with ``sections`` list, each containing ``entries``.
    """
    context = schema.get("@context", {})
    prefixes = _build_prefixes(context)

    sections: List[Dict[str, Any]] = []
    main_entries: List[Dict[str, Any]] = []

    for prop_name, prop_schema in schema.get("properties", {}).items():
        if prop_name == "type":
            continue  # consumed as classMapping, not rendered

        entry_id = "oold_" + prop_name
        oold_value = oold_doc.get(prop_name)

        if prop_schema.get("type") == "object":
            # ── Top-level object → its own section ───────────────────────────
            obj_oold = oold_value if isinstance(oold_value, dict) else {}
            section_entries: List[Dict[str, Any]] = []

            for child_name, child_schema in prop_schema.get("properties", {}).items():
                child_id = f"oold_{prop_name}_{child_name}"
                child_value = obj_oold.get(child_name)

                if child_schema.get("readOnly"):
                    continue
                if child_schema.get("type") == "object":
                    nested_values = child_value if isinstance(child_value, dict) else {}
                    section_entries.extend(
                        _flatten_object_to_entries(child_schema, child_id, context, prefixes, nested_values)
                    )
                elif child_schema.get("type") == "array" and child_schema.get("items", {}).get("type") == "object":
                    arr = _build_array_group_entry(child_name, child_schema, child_id, context, prefixes, child_value)
                    section_entries.append(arr)
                else:
                    e = _make_scalar_entry(child_id, child_name, child_schema, context, prefixes, child_value)
                    if e:
                        section_entries.append(e)

            sections.append({
                "id": f"oold_section_{prop_name}",
                "name": prop_schema.get("title", prop_name),
                "entries": section_entries,
            })

        elif prop_schema.get("type") == "array" and prop_schema.get("items", {}).get("type") == "object":
            # ── Top-level array-of-objects → ArrayGroup in main section ──────
            if prop_schema.get("readOnly"):
                continue
            arr = _build_array_group_entry(prop_name, prop_schema, entry_id, context, prefixes, oold_value)
            main_entries.append(arr)

        else:
            # ── Scalar / kitem / select / etc. → main section ────────────────
            e = _make_scalar_entry(entry_id, prop_name, prop_schema, context, prefixes, oold_value)
            if e:
                main_entries.append(e)

    # Always prepend the main section so it appears first
    if main_entries or not sections:
        sections.insert(0, {
            "id": "oold_section_0",
            "name": schema.get("title", "Details"),
            "entries": main_entries,
        })

    # x-transformers → inject a File upload entry at the top of the first section
    transformers = schema.get("x-transformers", [])
    if isinstance(transformers, str):
        transformers = [transformers]
    if transformers and sections:
        sections[0]["entries"].insert(0, {
            "id": "oold_file_upload",
            "label": "Instrument File",
            "type": "File",
        })

    return {"sections": sections}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def schema_to_oold(
    schema_url: str, input_data: Dict[str, Any]
) -> Dict[str, Any]:
    """Apply the simplified→OO-LD JSONata transform and return the OO-LD dict.

    Fetches ``specs/transform.simplified.jsonata`` from *schema_url* and
    evaluates it against *input_data*.  Returns *input_data* unchanged when
    the transform file does not exist (HTTP 404).

    Args:
        schema_url: URL from the ktype spec's ``semantic_schemas[].url`` field.
        input_data: Simplified input dict.

    Returns:
        OO-LD ontology dict (NOT the webform format).

    Raises:
        ImportError: If the ``jsonata`` package is not installed.
        requests.HTTPError: If fetching the transform file fails (non-404).
    """
    try:
        from jsonata.jsonata import Jsonata
    except ImportError as exc:
        raise ImportError(
            "The 'jsonata' package is required to apply simplified input "
            "transforms. Install it with: pip install jsonata"
        ) from exc

    specs_url = _to_raw_specs_url(schema_url)
    transform_url = f"{specs_url}/transform.simplified.jsonata"
    logger.debug("Fetching JSONata transform from %s", transform_url)
    response = requests.get(transform_url, timeout=30)

    if response.status_code == 404:
        logger.debug(
            "No simplified transform at %s — passing input through", transform_url
        )
        return input_data

    response.raise_for_status()
    return Jsonata(response.text).evaluate(input_data)


def schema_to_webform(
    schema_url: str, input_data: Dict[str, Any]
) -> Dict[str, Any]:
    """Convert a simplified input dict to the DSMS frontend webform format.

    Pipeline:

    1. Fetch ``schema.oold.yaml`` from *schema_url* and resolve ``allOf/$ref``
       inheritance chains.
    2. Apply ``specs/transform.simplified.jsonata`` (if present) to obtain the
       OO-LD ontology values from *input_data*.
    3. Build the webform ``{sections: [{entries: [...]}]}`` structure from the
       schema definition, filling entry values from the OO-LD output.

    When no transform file exists (HTTP 404) *input_data* is used as-is as the
    value source — callers may pass OO-LD or simplified dicts directly in that
    case.

    Args:
        schema_url: URL from the ktype spec's ``semantic_schemas[].url`` field.
                    GitHub blob URLs and raw content URLs are both accepted.
        input_data: Simplified input dict (or OO-LD dict when no transform).

    Returns:
        Webform dict with ``sections``/``entries`` format expected by the DSMS
        frontend semantic schema UI.

    Raises:
        ImportError: If PyYAML is not installed.
        requests.HTTPError: If fetching the schema or transform file fails.
    """
    try:
        import yaml as _yaml
    except ImportError as exc:
        raise ImportError(
            "PyYAML is required for OO-LD schema parsing. "
            "Install it with: pip install pyyaml"
        ) from exc

    raw_url = _to_raw_url(schema_url)
    logger.debug("Fetching OO-LD schema from %s", raw_url)
    resp = requests.get(raw_url, timeout=30)
    resp.raise_for_status()

    schema = _yaml.safe_load(resp.text)
    schema = _resolve_schema_refs(schema, raw_url)

    # Get OO-LD values (keys aligned with schema property names)
    oold_doc = schema_to_oold(schema_url, input_data)

    return _parse_oold_schema_to_webform(schema, oold_doc)
