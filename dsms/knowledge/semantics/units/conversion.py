"""DSMS Unit Semantics Conversion"""

from functools import lru_cache
from io import StringIO
from typing import Optional
from urllib.parse import urlparse

import requests
from rdflib import Graph


def _is_valid_url(url: str) -> bool:
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


def _sparql_symbol_from_iri(uri: str) -> str:
    return f"""PREFIX qudt: <http://qudt.org/schema/qudt/>
    SELECT DISTINCT ?symbol
        WHERE {{
            <{uri}> a qudt:Unit ;
                    qudt:ucumCode ?symbol .
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
def _get_symbol_from_uri(uri: str) -> str:
    graph = _get_qudt_graph("qudt_units")
    query = _sparql_symbol_from_iri(uri)
    symbol = [str(row["symbol"]) for row in graph.query(query)]
    if len(symbol) == 0:
        raise ValueError(f"No symbol found for unit with uri `{uri}`.")
    if len(symbol) > 1:
        raise ValueError(
            f"More than one symbol factor for unit with uri `{uri}`."
        )
    return symbol.pop()


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
