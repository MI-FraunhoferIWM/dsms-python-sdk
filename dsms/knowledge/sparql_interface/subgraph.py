"""DSMS Subgraph interface"""

from typing import TYPE_CHECKING

from dsms.knowledge.sparql_interface.utils import (
    _create_subgraph,
    _delete_subgraph,
    _get_subgraph,
    _update_subgraph,
)

if TYPE_CHECKING:
    from rdflib import Graph

    from dsms import DSMS


class Subgraph:
    """Subgraph interface for DSMS"""

    def __init__(self, dsms):
        """Initalize the Sparql interface"""
        self._dsms: "DSMS" = dsms

    def update(self, graph: "Graph", repository: str = "knowledge") -> None:
        """Update a subgraph in the DSMS"""
        _update_subgraph(graph, self._dsms.config.encoding, repository)

    def create(self, graph: "Graph", repository: str = "knowledge") -> None:
        """Create a subgraph in the DSMS"""
        _create_subgraph(graph, self._dsms.config.encoding, repository)

    def delete(self, identifier: str, repository: str = "knowledge") -> None:
        """Delete a subgraph in the DSMS"""
        _delete_subgraph(identifier, repository)

    def get(
        self,
        identifier: str,
        repository: str = "knowledge",
        is_kitem_id: bool = False,
    ) -> "Graph":
        """Get a subgraph from the DSMS"""
        return _get_subgraph(identifier, repository, is_kitem_id)
