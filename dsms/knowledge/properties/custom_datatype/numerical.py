"""Module for custom numerical data type"""

from typing import TYPE_CHECKING

from dsms.knowledge.semantics.units.utils import (
    get_conversion_factor,
    get_property_unit,
)

if TYPE_CHECKING:
    from typing import Any, Dict, Optional

    from dsms import KItem


class NumericalDataType(float):
    """Custom Base data type for custom properties"""

    def __init__(self, value) -> None:  # pylint: disable=unused-argument
        self._kitem: "Optional[KItem]" = None
        self._name: "Optional[str]" = None

    @property
    def kitem(cls) -> "Optional[KItem]":
        """Context of the current kitem for this property"""
        return cls._kitem

    @kitem.setter
    def kitem(cls, value: "Optional[KItem]") -> None:
        """Setter for current KItem context"""
        cls._kitem = value

    @property
    def name(cls) -> str:
        """Context of the name for this property"""
        return cls._name

    @name.setter
    def name(cls, value: str) -> None:
        """Setter for the name of the property"""
        cls._name = value

    def get_unit(self) -> "Dict[str, Any]":
        """Get unit for the property"""
        return get_property_unit(self.kitem.id, self.name)

    def convert_to(
        self,
        unit_symbol_or_iri: str,
        decimals: "Optional[int]" = None,
        use_input_iri: bool = False,
    ) -> float:
        """
        Convert the data of property to a different unit.

        Args:
            unit_symbol_or_iri (str): Symbol or IRI of the unit to convert to.
            decimals (Optional[int]): Number of decimals to round the result to. Defaults to None.
            use_input_iri (bool): If True, use IRI for unit comparison. Defaults to False.

        Returns:
            float: converted value of the property
        """
        unit = self.get_unit()
        if use_input_iri:
            input_str = unit.get("iri")
        else:
            input_str = unit.get("symbol")
        return self * get_conversion_factor(
            input_str, unit_symbol_or_iri, decimals=decimals
        )
