"""DSMS Subgraph interface"""

from typing import TYPE_CHECKING

from dsms.core.configuration import DEFAULT_REPO
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

    def update(self, graph: "Graph", repository: str = DEFAULT_REPO) -> None:
        """Update a subgraph in the DSMS"""
        _update_subgraph(
            self._dsms, graph, self._dsms.config.encoding, repository
        )

    def create(self, graph: "Graph", repository: str = DEFAULT_REPO) -> None:
        """Create a subgraph in the DSMS"""
        _create_subgraph(
            self._dsms, graph, self._dsms.config.encoding, repository
        )

    def delete(self, identifier: str, repository: str = DEFAULT_REPO) -> None:
        """Delete a subgraph in the DSMS"""
        _delete_subgraph(self._dsms, identifier, repository)

    def get(
        self,
        identifier: str,
        repository: str = DEFAULT_REPO,
        is_kitem_id: bool = False,
    ) -> "Graph":
        """Get a subgraph from the DSMS"""
        return _get_subgraph(self._dsms, identifier, repository, is_kitem_id)
