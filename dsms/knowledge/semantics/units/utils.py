"""Utilities for unit semantics of a KItem"""

from functools import lru_cache
from typing import TYPE_CHECKING

from .base import BaseUnitSparqlQuery
from .conversion import (
    _check_qudt_mapping,
    _get_factor_from_uri,
    _is_valid_url,
    _units_are_compatible,
)

if TYPE_CHECKING:
    from typing import Any, Dict, Optional, Union
    from uuid import UUID


@lru_cache
def get_conversion_factor(
    original_unit: str, target_unit: str, decimals: "Optional[int]" = None
) -> float:
    """
    Calculate the conversion factor between two compatible units.

    This function calculates the conversion factor between two units, specified
    by their URIs or labels. If the provided units are not valid URLs, the
    function attempts to check a QUDT (Quantities, Units, Dimensions, and Data
    Types in OWL and XML) mapping to retrieve the correct URI.

    Parameters:
        original_unit (str): The original unit to convert from, specified by URI or label.
        target_unit (str): The target unit to convert to, specified by URI or label.
        decimals (Optional[int]): An optional parameter specifying the number of
            decimal places to round the conversion factor to. Default is None,
            indicating no rounding.

    Returns:
        float: The conversion factor from the original unit to the target unit.

    Raises:
        ValueError: If the conversion factor cannot be determined due to invalid
            unit specifications, missing mapping in QUDT, or if the units are not
            compatible for conversion.

    Example:
        >>> get_conversion_factor('http://qudt.org/vocab/unit/M', 'http://qudt.org/vocab/unit/IN')
        39.3701
        >>> get_conversion_factor('m', 'in')
        39.3701
    """
    if not _is_valid_url(original_unit):
        original_unit = _check_qudt_mapping(original_unit)
    if not _is_valid_url(target_unit):
        target_unit = _check_qudt_mapping(target_unit)
    if not _units_are_compatible(original_unit, target_unit):
        raise ValueError(
            f"Unit {original_unit} can numerically not be converted into {target_unit}"
        )
    factor = _get_factor_from_uri(original_unit) / _get_factor_from_uri(
        target_unit
    )
    if decimals:
        factor = round(factor, decimals)
    return factor


def get_property_unit(
    kitem_id: "Union[str, UUID]",
    property_name: str,
    is_dataframe_column: bool = False,
    autocomplete_symbol: bool = True,
) -> "Dict[str, Any]":
    """
    Retrieve the unit associated with a given property of a KIitem.

    Args:
        kitem (KItem): The identifier of the KItem.
        property_name (str): The name of the property of the KItem  for which
            the unit is to be retrieved.
        is_dataframe_column (bool, optional): Indicates whether the property is an DataFrame
            column or a custom property. Defaults to False.
        autocomplete_symbol (bool, optional): Whether the symbol of a unit shall be
            fetched automatically from the ontology when it is not given next to the
            URI.

    Returns:
        Dict[str, Any]: A dictionary with the symbol and iri of the unit associated
            with the specified property.

    Raises:
        ValueError: If unable to retrieve the unit for the property due to any errors or if
            the property does not have a unit or has more than one unit associated with it.
    """
    from dsms import Context

    units_sparql_object = Context.dsms.config.units_sparql_object
    if not issubclass(units_sparql_object, BaseUnitSparqlQuery):
        raise TypeError(
            f"´{units_sparql_object}´ must be a subclass of `{BaseUnitSparqlQuery}`"
        )
    try:
        query = units_sparql_object(
            kitem_id=kitem_id,
            property_name=property_name,
            is_dataframe_column=is_dataframe_column,
            autocomplete_symbol=autocomplete_symbol,
        )
    except Exception as error:
        raise ValueError(
            f"Something went wrong catching the unit for property `{property_name}`."
        ) from error
    if len(query.results) == 0:
        raise ValueError(
            f"""Property `{property_name}` does not own any
            unit with respect to the semantics applied."""
        )
    if len(query.results) > 1:
        raise ValueError(
            f"""Property `{property_name}` owns more than one
            unit with respect to the semantics applied."""
        )
    return query.results.pop()
