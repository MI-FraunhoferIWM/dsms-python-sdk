"""Sparql interface implementation for the DSMS"""

from typing import TYPE_CHECKING

from dsms.knowledge.sparql_interface.utils import (
    _add_rdf,
    _sparql_query,
    _sparql_update,
)

if TYPE_CHECKING:
    from typing import Any, Dict

    from dsms.core.dsms import DSMS


class SparqlInterface:

    """Sparql Interface for the DSMS."""

    def __init__(self, dsms):
        """Initalize the Sparql interface"""
        self._dsms: "DSMS" = dsms

    def query(
        self, query: str, repository: str = "knowledge"
    ) -> "Dict[str, Any]":
        """Perform Sparql Query"""
        return _sparql_query(query, repository)

    def update(self, filepath: str, repository: str = "knowledge") -> None:
        """Perform update query from local file"""
        _sparql_update(filepath, self._dsms.config.encoding, repository)

    def add_rdf(self, filepath: str, repository: str = "knowledge") -> None:
        """Upload RDF to triplestore from local file"""
        _add_rdf(filepath, self._dsms.config.encoding, repository)
