"""Sparql interface utilities for the DSMS"""
import io
from typing import TYPE_CHECKING

from rdflib import Graph
from rdflib.plugins.sparql.results.jsonresults import JSONResult

from dsms.core.utils import _kitem_id2uri, _perform_request

if TYPE_CHECKING:
    from typing import Any, Dict, Optional, TextIO, Union

    from dsms import DSMS


def _sparql_query(
    dsms: "DSMS", query: str, repository: str
) -> "Dict[str, Any]":
    """Submit plain SPARQL-query to the DSMS instance."""
    response = _perform_request(
        dsms,
        "api/knowledge/sparql",
        "post",
        data={"query": query},
        params={"repository": repository},
    )
    if not response.ok:
        raise RuntimeError(f"Sparql was not successful: {response.text}")
    try:
        response = response.json()
    except Exception as excep:
        raise RuntimeError(
            f"""Something went wrong fetching injecting sparql-query:
            \n
            `{query}`"""
        ) from excep
    return response


def _sparql_update(
    dsms: "DSMS",
    file_or_pathlike: "Union[str, TextIO]",
    encoding: str,
    repository: str,
) -> None:
    """Submit plain SPARQL-query to the DSMS instance."""
    response = _perform_request(
        dsms,
        "api/knowledge/update-query",
        "post",
        files=_get_file_or_pathlike(file_or_pathlike, encoding),
        params={"repository": repository},
    )
    if not response.ok:
        raise RuntimeError(f"Sparql was not successful: {response.text}")


def _get_file_or_pathlike(
    file_or_pathlike: "Union[str, TextIO]", encoding: str
) -> "TextIO":
    if isinstance(file_or_pathlike, str):
        files = {
            "file": open(  # pylint: disable=R1732
                file_or_pathlike, mode="r+", encoding=encoding
            )
        }
    else:
        if "read" not in dir(file_or_pathlike):
            raise TypeError(
                f"{file_or_pathlike} is neither a path"
                f"or a file-like object."
            )
        files = {"file": file_or_pathlike}
    return files


def _add_rdf(
    dsms: "DSMS",
    file_or_pathlike: "Union[str, TextIO]",
    encoding: str,
    repository: str,
    context: "Optional[str]" = None,
) -> None:
    """Create the subgraph in the remote backend"""
    params = {"repository": repository}
    if context:
        params["context"] = context
    response = _perform_request(
        dsms,
        "api/knowledge/add-rdf",
        "post",
        files=_get_file_or_pathlike(file_or_pathlike, encoding),
        params=params,
    )
    if not response.ok:
        raise RuntimeError(
            f"Not able to create subgraph in backend: {response.text}"
        )


def _delete_subgraph(dsms: "DSMS", identifier: str, repository: str) -> None:
    """Get subgraph related to a certain dataset id."""
    query = f"""
    DELETE {{
        ?s ?p ?o
    }}
    WHERE {{
        BIND(
            <{identifier}> as ?g
            )
        {{
            GRAPH ?g {{ ?s ?p ?o . }}
        }}
    }}"""
    response = _sparql_query(dsms, query, repository)
    if not response.get("boolean"):
        raise RuntimeError(
            f"Deleteing subgraph was not successful: {response}"
        )


def _create_subgraph(
    dsms: "DSMS", graph: "Graph", encoding: str, respository: str
) -> None:
    """Create the subgraph in the remote backend"""
    upload_file = io.BytesIO(graph.serialize(encoding=encoding))
    _add_rdf(
        dsms,
        upload_file,
        encoding,
        respository,
        context=f"<{graph.identifier}>",
    )


def _update_subgraph(
    dsms: "DSMS", graph: "Graph", encoding: str, repository: str
) -> None:
    """Update the subgraph in the remote backend"""
    _delete_subgraph(dsms, graph.identifier, repository)
    _create_subgraph(dsms, graph, encoding, repository)


def _get_subgraph(
    dsms: "DSMS", identifier: str, repository: str, is_kitem_id: bool = False
) -> "Graph":
    """Get subgraph related to a certain dataset id."""
    if is_kitem_id:
        identifier = _kitem_id2uri(dsms, identifier)
    query = f"""
    SELECT DISTINCT
        ?s ?p ?o
    WHERE {{
        BIND(
            <{identifier}> as ?g
            )
        {{
            GRAPH ?g {{ ?s ?p ?o . }}
        }}
    }}"""

    graph = Graph(identifier=identifier)
    data = _sparql_query(dsms, query, repository)
    for row in JSONResult(data).bindings:
        graph.add(row.values())

    if len(graph) == 0:
        raise ValueError(f"Subgraph for id `{identifier}` does not exist.")

    return graph
