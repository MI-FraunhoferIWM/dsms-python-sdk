"""DSMS Unit Semantics Conversion"""

import tempfile
from functools import lru_cache
from typing import List, Optional
from urllib.parse import urlparse

import requests
from rdflib import Graph


def _is_valid_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False


def _qudt_sparql(symbol: str) -> str:
    return f"""PREFIX qudt: <http://qudt.org/schema/qudt/>
    SELECT DISTINCT ?unit
        WHERE {{
            ?unit a qudt:Unit .
            {{
                ?unit qudt:symbol "{symbol}" .
            }}
            UNION
            {{
                ?unit qudt:ucumCode "{symbol}"^^qudt:UCUMcs .
            }}
        }}"""


def _qudt_sparql_factor(uri: str) -> str:
    return f"""PREFIX qudt: <http://qudt.org/schema/qudt/>
    SELECT DISTINCT ?factor
        WHERE {{
            <{uri}> a qudt:Unit ;
                    qudt:conversionMultiplier ?factor .
        }}"""


@lru_cache
def _get_qudt_ontology() -> requests.Response:
    from dsms import Context

    url = Context.dsms.config.qudt_uri
    response = requests.get(url, timeout=Context.dsms.config.request_timeout)
    if response.status_code != 200:
        raise RuntimeError(
            f"Could not download QUDT ontology. Please check URI: {url}"
        )
    response.encoding = "utf-8"
    return response


def _to_tempfile(content) -> str:
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".ttl", delete=False, encoding="utf-8"
    ) as tmp:
        tmp.write(content)
    return tmp.name


@lru_cache
def _get_qudt_graph() -> Graph:
    response = _get_qudt_ontology()
    file = _to_tempfile(response.text)

    graph = Graph()
    graph.parse(file, encoding="utf-8")
    return graph


@lru_cache
def _get_query_match(symbol: str) -> List[str]:
    graph = _get_qudt_graph()
    query = _qudt_sparql(symbol)
    return [str(row["unit"]) for row in graph.query(query)]


def _check_qudt_mapping(symbol: str) -> Optional[str]:
    match = _get_query_match(symbol)
    if len(match) == 0:
        raise ValueError(
            f"No QUDT Mapping found for unit with symbol `{symbol}`."
        )
    if len(match) > 1:
        raise ValueError(
            f"More than one QUDT Mapping found for unit with symbol `{symbol}`."
        )
    return match.pop()


@lru_cache
def get_conversion_factor(original_unit: str, target_unit: str) -> float:
    """
    Calculate the conversion factor between two units.

    This function calculates the conversion factor between two units, specified
    by their URIs or labels. If the provided units are not valid URLs, the
    function attempts to check a QUDT (Quantities, Units, Dimensions, and Data
    Types in OWL and XML) mapping to retrieve the correct URI.

    Parameters:
        original_unit (str): The original unit to convert from, specified by URI or unit symbol.
        target_unit (str): The target unit to convert to, specified by URI or label.

    Returns:
        float: The conversion factor from the original unit to the target unit.

    Raises:
        ValueError: If the conversion factor cannot be determined due to invalid
            unit specifications or missing mapping in QUDT.

    Example:
        >>> get_conversion_factor('http://qudt.org/vocab/unit/M', 'http://qudt.org/vocab/unit/IN')
        39.3701
        >>> get_conversion_factor('m', 'in')
        39.3701
    """
    if not _is_valid_url(original_unit):
        original_unit = _check_qudt_mapping(original_unit)
    if not _is_valid_url(target_unit):
        target_unit = _check_qudt_mapping(target_unit)
    return _get_factor_from_uri(original_unit) / _get_factor_from_uri(
        target_unit
    )


@lru_cache
def _get_factor_from_uri(uri: str) -> int:
    graph = _get_qudt_graph()
    query = _qudt_sparql_factor(uri)
    factor = [float(row["factor"]) for row in graph.query(query)]
    if len(factor) == 0:
        raise ValueError(f"No conversion factor for unit with uri `{uri}`.")
    if len(factor) > 1:
        raise ValueError(
            f"More than one conversion factor for unit with uri `{uri}`."
        )
    return factor.pop()
