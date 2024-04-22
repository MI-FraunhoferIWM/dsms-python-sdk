"""DSMS acstract class for units sparql query"""

from typing import TYPE_CHECKING

from dsms.knowledge.semantics.queries import BaseSparqlQuery

if TYPE_CHECKING:
    from typing import Any, Dict, Union
    from uuid import UUID


class BaseUnitSparqlQuery(BaseSparqlQuery):
    """
    Abstract class for defining sparql queries fetching
    the units of a hdf5 column or custom property of
    a kitem.
    """

    def __init__(
        self,
        kitem_id: "Union[str, UUID]",
        property_name: str,
        is_hdf5_column: bool = False,
        autocomplete_symbol: bool = True,
    ) -> None:
        super().__init__(
            kitem_id=kitem_id,
            property_name=property_name,
            is_hdf5_column=is_hdf5_column,
            autocomplete_symbol=autocomplete_symbol,
        )

    # OVERRIDE
    @property
    def result_mappings(cls) -> "Dict[str, Any]":
        """Define mappings for the results of the units sparql queries"""
        return {"symbol": str, "iri": str}
