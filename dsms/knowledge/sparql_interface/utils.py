"""Sparql interface utilities for the DSMS"""
import io
from typing import TYPE_CHECKING

from rdflib import Graph

from dsms.core.utils import _kitem_id2uri, _perform_request

if TYPE_CHECKING:
    from typing import Any, Dict, TextIO, Union


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
    return response["results"]["bindings"]


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
    print(files)
    return files


def _add_rdf(
    file_or_pathlike: "Union[str, TextIO]", encoding: str, repository: str
) -> None:
    """Create the subgraph in the remote backend"""
    response = _perform_request(
        "api/knowledge/add-rdf",
        "post",
        files=_get_file_or_pathlike(file_or_pathlike, encoding),
        params={"repository": repository},
    )
    if not response.ok:
        raise RuntimeError(
            f"Not able to create subgraph in backend: {response.text}"
        )


def _delete_subgraph(identifier: str, encoding: str, repository: str) -> None:
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
    _sparql_update(query, encoding, repository)


def _update_subgraph(graph: Graph, encoding: str, repository: str) -> None:
    """Update the subgraph in the remote backend"""
    _delete_subgraph(graph.identifier, encoding, repository)
    _add_rdf(graph, encoding, repository)


def _get_subgraph(kitem_id: str, repository: str) -> Graph:
    """Get subgraph related to a certain dataset id."""
    uri = _kitem_id2uri(kitem_id)
    query = f"""
    SELECT DISTINCT
        ?s ?p ?o
    WHERE {{
        BIND(
            <{uri}> as ?g
            )
        {{
            GRAPH ?g {{ ?s ?p ?o . }}
        }}
    }}"""
    data = _sparql_query(query, repository)

    buffer = io.StringIO()
    buffer.writelines(
        f"<{row['s']['value']}> <{row['p']['value']}> <{row['o']['value']}> ."
        for row in data
    )
    buffer.seek(0)

    graph = Graph(identifier=uri)
    graph.parse(buffer, format="n3")

    if len(graph) == 0:
        raise ValueError(f"Subgraph for id `{kitem_id}` does not exist.")

    return graph
