"""DSMS Base Abstract Class for Queries"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from rdflib.plugins.sparql.results.jsonresults import JSONResult

if TYPE_CHECKING:
    from typing import Any, Dict, Optional

    from dsms import DSMS


class BaseSparqlQuery(ABC):
    """Abstract class for DSMS Sparql Query"""

    def __init__(self, **kwargs: "Dict[str, Any]") -> None:
        from dsms import Session

        self._kwargs = kwargs
        self._results: "Optional[Dict[str, Any]]" = None
        self._dsms: "DSMS" = Session.dsms

        self.execute()

    @property
    def kwargs(self) -> "Dict[str, Any]":
        """Return kwargs passed during initialization"""
        return self._kwargs

    @property
    def dsms(self) -> "Dict[str, Any]":
        """Return dsms context"""
        return self._dsms

    @property
    def results(self) -> "Optional[Dict[str, Any]]":
        """Return query results"""
        return self._results

    @property
    @abstractmethod
    def result_mappings(self) -> "Dict[str, Any]":
        """
        Define a mapping between the output keys and the output datatype.
        E.g. {'foo': int, 'bar': str, 'foobar': MyCustomClass}
        """

    @property
    @abstractmethod
    def query(self) -> str:
        """
        Define sparql query by using the kwargs defined during initialization.
        """

    @abstractmethod
    def postprocess_result(self, row: "Dict[str, Any]") -> "Dict[str, Any]":
        """
        Define a function that postprocesses the result of the indivudal row in the
        sparql result. This might e.g. be some string operations etc.
        """

    def execute(self) -> None:
        """Execute sparql query and bind results."""
        result = self.dsms.sparql_interface.query(self.query)
        self._results = []
        for row in JSONResult(result).bindings:
            row_converted = {str(key): value for key, value in row.items()}
            self._results.append(
                self.postprocess_result(
                    {
                        name: func(row_converted.get(name))
                        for name, func in self.result_mappings.items()
                    }
                )
            )
