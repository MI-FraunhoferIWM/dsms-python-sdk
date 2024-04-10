"""Semantic units for a custom property of a KItem in DSMS"""

from urllib.parse import urljoin

from dsms.knowledge.semantics.units.base import BaseUnitSparqlQuery


class UnitSparqlQuery(BaseUnitSparqlQuery):
    """
    Define a sparql query for fetching the units of an HDf5 column of a KItem
    """

    # OVERRIDE
    @property
    def query(cls) -> str:
        """Construct sparql query for getting unit for hdf5 column"""
        kitem_id = cls.kwargs.get("kitem_id")
        property_name = cls.kwargs.get("property_name")
        if not kitem_id:
            raise ValueError("KItem ID must be defined.")
        if not property_name:
            raise ValueError("Property name must be defined.")
        url = urljoin(str(cls.dsms.config.host_url), str(kitem_id))

        if cls.kwargs.get("is_hdf5_column"):
            query = f"""
            prefix datamodel: <http://emmo.info/datamodel#>
            prefix metro: <http://emmo.info/emmo/middle/metrology#>
            prefix math: <http://emmo.info/emmo/middle/math#>
            prefix perceptual: <http://emmo.info/emmo/middle/perceptual#>
            prefix reductionistic: <http://emmo.info/emmo/middle/reductionistic#>

            select distinct
                (STR(?symbol_literal) as ?symbol)
                ?iri
            where {{

                <{url}/dataset> datamodel:composition ?prop .

                ?prop rdfs:label "{property_name}" ;
                rdf:type datamodel:DataInstance ;
                metro:EMMO_67fc0a36_8dcb_4ffa_9a43_31074efa3296 ?literal, ?unit .
            ?unit rdf:type ?iri .
            ?literal a metro:UnitLiteral ;
                     metro:EMMO_67fc0a36_8dcb_4ffa_9a43_31074efa3296 ?symbol_literal .
            FILTER(?iri != metro:UnitLiteral)
            }}
            """

        else:
            query = f"""
            prefix datamodel: <http://emmo.info/datamodel#>
            prefix metro: <http://emmo.info/emmo/middle/metrology#>
            prefix math: <http://emmo.info/emmo/middle/math#>
            prefix perceptual: <http://emmo.info/emmo/middle/perceptual#>
            prefix reductionistic: <http://emmo.info/emmo/middle/reductionistic#>

            select distinct
                ?symbol
                ?iri
            where {{

                <{url}/dataset> datamodel:composition ?prop .

                ?prop rdfs:label "{property_name}" ;
                    rdf:type datamodel:Metadata ;
                    metro:EMMO_8ef3cd6d_ae58_4a8d_9fc0_ad8f49015cd0 ?numeric .

                ?numeric rdf:type math:EMMO_4ce76d7f_03f8_45b6_9003_90052a79bfaa ;
                        metro:EMMO_67fc0a36_8dcb_4ffa_9a43_31074efa3296 ?unit , ?literal .

                ?unit rdf:type ?iri .
                ?literal a metro:UnitLiteral ;
                        metro:EMMO_67fc0a36_8dcb_4ffa_9a43_31074efa3296 ?symbol_literal .
                FILTER(?iri != metro:UnitLiteral)
                }}
            """
        return query
