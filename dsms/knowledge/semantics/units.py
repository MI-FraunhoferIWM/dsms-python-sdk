"""DSMS Unit Semantics Conversion"""

from functools import lru_cache
from io import StringIO
from typing import Optional
from urllib.parse import urlparse

import requests
from rdflib import Graph


@lru_cache
def get_conversion_factor(
    original_unit: str, target_unit: str, rounded: Optional[int] = None
) -> float:
    """
    Calculate the conversion factor between two compatible units.

    This function calculates the conversion factor between two units, specified
    by their URIs or labels. If the provided units are not valid URLs, the
    function attempts to check a QUDT (Quantities, Units, Dimensions, and Data
    Types in OWL and XML) mapping to retrieve the correct URI.

    Parameters:
        original_unit (str): The original unit to convert from, specified by URI or label.
        target_unit (str): The target unit to convert to, specified by URI or label.
        rounded (Optional[int]): An optional parameter specifying the number of
            decimal places to round the conversion factor to. Default is None,
            indicating no rounding.

    Returns:
        float: The conversion factor from the original unit to the target unit.

    Raises:
        ValueError: If the conversion factor cannot be determined due to invalid
            unit specifications, missing mapping in QUDT, or if the units are not
            compatible for conversion.

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
    if not _units_are_compatible(original_unit, target_unit):
        raise ValueError(
            f"Unit {original_unit} can numerically not be converted into {target_unit}"
        )
    factor = _get_factor_from_uri(original_unit) / _get_factor_from_uri(
        target_unit
    )
    if rounded:
        factor = round(factor, rounded)
    return factor


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


def _qudt_sparql_quantity(original_uri: str, target_uri: str) -> str:
    return f"""PREFIX qudt: <http://qudt.org/schema/qudt/>
    SELECT DISTINCT ?kind
        WHERE {{
            ?kind a qudt:QuantityKind ;
                  qudt:applicableUnit <{original_uri}> , <{target_uri}> .
        }}"""


@lru_cache
def _units_are_compatible(
    original_uri: str, target_uri: str
) -> Optional[bool]:
    graph = _get_qudt_graph("qudt_quantity_kinds")
    query = _qudt_sparql_quantity(original_uri, target_uri)
    quantity = [str(row["kind"]) for row in graph.query(query)]
    if len(quantity) == 0:
        are_compatiable = False
    else:
        are_compatiable = True
    return are_compatiable


@lru_cache
def _check_qudt_mapping(symbol: str) -> Optional[str]:
    graph = _get_qudt_graph("qudt_units")
    query = _qudt_sparql(symbol)
    match = [str(row["unit"]) for row in graph.query(query)]
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
def _get_factor_from_uri(uri: str) -> int:
    graph = _get_qudt_graph("qudt_units")
    query = _qudt_sparql_factor(uri)
    factor = [float(row["factor"]) for row in graph.query(query)]
    if len(factor) == 0:
        raise ValueError(f"No conversion factor for unit with uri `{uri}`.")
    if len(factor) > 1:
        raise ValueError(
            f"More than one conversion factor for unit with uri `{uri}`."
        )
    return factor.pop()


@lru_cache
def _get_qudt_graph(ontology_ref: str) -> Graph:
    from dsms import Context

    url = getattr(Context.dsms.config, ontology_ref)
    encoding = Context.dsms.config.encoding
    graph = Graph()

    response = requests.get(url, timeout=Context.dsms.config.request_timeout)
    if response.status_code != 200:
        raise RuntimeError(
            f"Could not download QUDT ontology. Please check URI: {url}"
        )
    response.encoding = encoding

    with StringIO() as tmp:
        tmp.write(response.text)
        tmp.seek(0)
        graph.parse(tmp, encoding=encoding)

    return graph
