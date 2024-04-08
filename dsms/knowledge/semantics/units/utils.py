"""Utilities for unit semantics of a KItem"""

from .conversion import _is_valid_url, _check_qudt_mapping, _units_are_compatible, _get_factor_from_uri
from .sparql import UnitSparqlQuery
from typing import TYPE_CHECKING
from functools import lru_cache

if TYPE_CHECKING:
    from typing import Optional, Dict, Any, Union
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

def get_property_unit(kitem_id: "Union[str, UUID]", property_name: str, is_hdf5_column: bool = False) -> "Dict[str, Any]":
    """
    Retrieve the unit associated with a given property of a KIitem.

    Args:
        kitem (KItem): The identifier of the KItem.
        property_name (str): The name of the property of the KItem  for which
            the unit is to be retrieved.
        is_hdf5_column (bool, optional): Indicates whether the property is an HDF5
            column or a custom property. Defaults to False.

    Returns:
        Dict[str, Any]: A dictionary with the symbol and iri of the unit associated 
            with the specified property.

    Raises:
        ValueError: If unable to retrieve the unit for the property due to any errors or if
            the property does not have a unit or has more than one unit associated with it.
    """
    try:
        query = UnitSparqlQuery(kitem_id, property_name, is_hdf5_column)
    except Exception as error:
        raise ValueError(f"Something went wrong catching the unit for property `{property_name}`.") from error
    if len(query.results) == 0:
        raise ValueError(f"Property `{property_name}` does not own any unit with respect to the semantics applied.")
    elif len(query.results) > 1:
        raise ValueError(f"Property `{property_name}` owns more than one unit with respect to the semantics applied.")
    return query.results.pop()