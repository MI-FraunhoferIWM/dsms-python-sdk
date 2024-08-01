"""Semantic units for a custom property of a KItem in DSMS"""

from typing import TYPE_CHECKING
from urllib.parse import urljoin

from dsms.knowledge.semantics.units.base import BaseUnitSparqlQuery

from .conversion import _get_symbol_from_uri

if TYPE_CHECKING:
    from typing import Any, Dict


class UnitSparqlQuery(BaseUnitSparqlQuery):
    """
    Define a sparql query for fetching the units of an HDf5 column of a KItem
    """

    # OVERRIDE
    @property
    def query(cls) -> str:
        """Construct sparql query for getting unit for dataframe column"""
        kitem_id = cls.kwargs.get("kitem_id")
        property_name = cls.kwargs.get("property_name")
        if not kitem_id:
            raise ValueError("KItem ID must be defined.")
        if not property_name:
            raise ValueError("Property name must be defined.")
        url = urljoin(str(cls.dsms.config.host_url), str(kitem_id))

        return f"""prefix csvw: <http://www.w3.org/ns/csvw#>
            prefix dcat: <http://www.w3.org/ns/dcat#>
            prefix qudt: <http://qudt.org/schema/qudt/>
            prefix xsd: <http://www.w3.org/2001/XMLSchema#>
            prefix fileid: <{url}/>
            select distinct ?iri
            where {{
                bind(
                    <{url}> as ?g
                    )
                {{
                    graph ?g {{
                        fileid:{property_name} qudt:hasUnit ?iri .
                    }}
                }}
        }}"""

    # OVERRIDE
    def postprocess_result(cls, row: "Dict[str, Any]") -> "Dict[str, Any]":
        """
        Define a function that postprocesses the result of the indivudal row in the
        sparql result. This might e.g. be some string operations etc.
        """
        if row.get("symbol") == "None":
            row["symbol"] = None
        if cls.kwargs.get("autocomplete_symbol") and not row.get("symbol"):
            row["symbol"] = _get_symbol_from_uri(row.get("iri"))
        return row
