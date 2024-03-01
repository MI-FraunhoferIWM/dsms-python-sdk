"""Sparql interface utilities for the DSMS"""
import io
from typing import TYPE_CHECKING

from rdflib.plugins.sparql.results.jsonresults import JSONResult

from dsms.core.utils import _kitem_id2uri, _perform_request

if TYPE_CHECKING:
    from typing import Any, Dict, Optional, TextIO, Union

    from rdflib import Graph


def _sparql_query(query: str, repository: str) -> "Dict[str, Any]":
    """Submit plain SPARQL-query to the DSMS instance."""
    response = _perform_request(
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
    file_or_pathlike: "Union[str, TextIO]",
    encoding: str,
    repository: str,
) -> None:
    """Submit plain SPARQL-query to the DSMS instance."""
    response = _perform_request(
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
        with open(file_or_pathlike, mode="r+", encoding=encoding) as file:
            files = {"file", file}
    else:
        if "read" not in dir(file_or_pathlike):
            raise TypeError(
                f"{file_or_pathlike} is neither a path"
                f"or a file-like object."
            )
        files = {"file": file_or_pathlike}
    return files


def _add_rdf(
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
        "api/knowledge/add-rdf",
        "post",
        files=_get_file_or_pathlike(file_or_pathlike, encoding),
        params=params,
    )
    if not response.ok:
        raise RuntimeError(
            f"Not able to create subgraph in backend: {response.text}"
        )


def _delete_subgraph(identifier: str, repository: str) -> None:
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
    response = _sparql_query(query, repository)
    if not response.get("boolean"):
        raise RuntimeError(
            f"Deleteing subgraph was not successful: {response}"
        )


def _create_subgraph(graph: "Graph", encoding: str, respository: str) -> None:
    """Create the subgraph in the remote backend"""
    upload_file = io.BytesIO(graph.serialize(encoding=encoding))
    _add_rdf(
        upload_file, encoding, respository, context=f"<{graph.identifier}>"
    )


def _update_subgraph(graph: "Graph", encoding: str, repository: str) -> None:
    """Update the subgraph in the remote backend"""
    _delete_subgraph(graph.identifier, repository)
    _create_subgraph(graph, encoding, repository)


def _get_subgraph(
    identifier: str, repository: str, is_kitem_id: bool = False
) -> "Graph":
    """Get subgraph related to a certain dataset id."""
    if is_kitem_id:
        identifier = _kitem_id2uri(identifier)
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
    data = _sparql_query(query, repository)
    graph = JSONResult(data)
    graph.identifier = identifier

    if len(graph) == 0:
        raise ValueError(f"Subgraph for id `{identifier}` does not exist.")

    return graph
