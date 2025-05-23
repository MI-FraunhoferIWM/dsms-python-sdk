"""Sparql interface implementation for the DSMS"""

from typing import TYPE_CHECKING

from dsms.core.configuration import DEFAULT_REPO
from dsms.knowledge.sparql_interface.subgraph import Subgraph
from dsms.knowledge.sparql_interface.utils import (
    _add_rdf,
    _sparql_query,
    _sparql_update,
)

if TYPE_CHECKING:
    from typing import Any, Dict, TextIO, Union

    from dsms.core.dsms import DSMS


class SparqlInterface:

    """Sparql Interface for the DSMS."""

    def __init__(self, dsms):
        """Initalize the Sparql interface"""
        self._dsms: "DSMS" = dsms
        self._subgraph = Subgraph(dsms)

    def query(
        self, query: str, repository: str = DEFAULT_REPO
    ) -> "Dict[str, Any]":
        """Perform Sparql Query"""
        return _sparql_query(self._dsms, query, repository)

    def update(
        self,
        file_or_pathlike: "Union[str, TextIO]",
        repository: str = DEFAULT_REPO,
    ) -> None:
        """Perform update query from local file"""
        _sparql_update(
            self._dsms,
            file_or_pathlike,
            self._dsms.config.encoding,
            repository,
        )

    def insert(
        self,
        file_or_pathlike: "Union[str, TextIO]",
        repository: str = DEFAULT_REPO,
    ) -> None:
        """Upload RDF to triplestore from local file"""
        _add_rdf(
            self._dsms,
            file_or_pathlike,
            self._dsms.config.encoding,
            repository,
        )

    @property
    def subgraph(self) -> Subgraph:
        """Subgraph interface for DSMS"""
        return self._subgraph
