"""Module for custom numerical data type"""

import logging
from typing import TYPE_CHECKING

from dsms.knowledge.semantics.units.utils import (
    get_conversion_factor,
    get_property_unit,
)

if TYPE_CHECKING:
    from typing import Any, Dict, Generator, Optional

    from dsms import KItem


logger = logging.Logger(__name__)


class NumericalDataType(float):
    """Custom Base data type for custom properties"""

    def __new__(cls, value):
        obj = super().__new__(cls, value)
        obj._kitem = None
        obj._name = None
        return obj

    def __str__(self) -> str:
        """Pretty print the numerical datatype"""
        if self.kitem.dsms.config.display_units:  # pylint: disable=no-member
            try:
                string = f"{self.__float__()} {self.get_unit().get('symbol')}"
            except Exception as error:
                logger.debug(
                    "Could not fetch unit from `%i`: %i", self.name, error.args
                )
                string = str(self.__float__())
        else:
            string = str(self.__float__())
        return string

    @classmethod
    def __get_validators__(cls) -> "Generator":
        yield cls.validate

    @classmethod
    def validate(cls, v: "Any") -> "NumericalDataType":
        """
        Validate the input value as a valid NumericalDataType.

        Args:
            v (Any): The value to be validated.

        Returns:
            NumericalDataType: An instance of NumericalDataType if validation is successful.

        Raises:
            TypeError: If the input value is not a float or int.
        """
        if not isinstance(v, (float, int)):
            raise TypeError(f"Expected float or int, got {type(v)}")
        obj = super().__new__(cls, v)
        obj._kitem = None
        obj._name = None
        return obj

    def __repr__(self) -> str:
        return str(self)

    @property
    def kitem(self) -> "Optional[KItem]":
        """Context of the current kitem for this property"""
        return self._kitem

    @kitem.setter
    def kitem(self, value: "Optional[KItem]") -> None:
        """Setter for current KItem context"""
        self._kitem = value

    @property
    def name(self) -> str:
        """Context of the name for this property"""
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        """Setter for the name of the property"""
        self._name = value

    def get_unit(self) -> "Dict[str, Any]":
        """Get unit for the property"""
        return get_property_unit(
            self.kitem.id,  # pylint: disable=no-member
            self.name,
            is_dataframe_column=True,
            autocomplete_symbol=self.kitem.dsms.config.autocomplete_units,  # pylint: disable=no-member
        )

    def convert_to(
        self,
        unit_symbol_or_iri: str,
        decimals: "Optional[int]" = None,
        use_input_iri: bool = True,
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
