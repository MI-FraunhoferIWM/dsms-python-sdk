"""Semantic units for a custom property of a KItem in DSMS"""

from typing import TYPE_CHECKING
from urllib.parse import quote, urljoin

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
    def query(self) -> str:
        """Construct sparql query for getting unit of a dataframe column or custom property.

        Supports two KG representations via UNION:
        - New format: csvw:Column nodes identified by csvw:name (column subject IRI is
          auto-generated and not derivable from the column name).
        - Old format: property nodes identified by IRI <kitem_url/PropertyName> with
          qudt:hasUnit as either an IRI or xsd:anyURI literal.
        """
        kitem_id = self.kwargs.get("kitem_id")
        property_name = self.kwargs.get("property_name")
        if not kitem_id:
            raise ValueError("KItem ID must be defined.")
        if not property_name:
            raise ValueError("Property name must be defined.")
        url = urljoin(str(self.dsms.config.host_url), str(kitem_id))
        # URL-encode for the old-format IRI branch: spaces/parens in property names
        # produce invalid SPARQL IRIs and cause the entire query to be rejected.
        encoded_name = quote(str(property_name), safe="")

        return f"""prefix csvw: <http://www.w3.org/ns/csvw#>
            prefix qudt: <http://qudt.org/schema/qudt/>
            select distinct ?iri
            where {{
                bind(<{url}> as ?g)
                {{
                    graph ?g {{
                        {{
                            ?col csvw:name "{property_name}" ;
                                 qudt:hasUnit ?iri .
                        }}
                        UNION
                        {{
                            <{url}/{encoded_name}> qudt:hasUnit ?iri .
                        }}
                    }}
                }}
        }}"""

    # OVERRIDE
    def postprocess_result(self, row: "Dict[str, Any]") -> "Dict[str, Any]":
        """
        Define a function that postprocesses the result of the indivudal row in the
        sparql result. This might e.g. be some string operations etc.
        """
        if row.get("symbol") == "None":
            row["symbol"] = None
        if self.kwargs.get("autocomplete_symbol") and not row.get("symbol"):
            row["symbol"] = _get_symbol_from_uri(row.get("iri"))
        return row
