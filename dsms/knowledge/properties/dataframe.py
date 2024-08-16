"""DataFrame property of a KItem"""
import logging
from typing import TYPE_CHECKING

import pandas as pd
from pydantic import Field

from dsms.knowledge.properties.base import KItemProperty, KItemPropertyList
from dsms.knowledge.utils import _get_dataframe_column, _is_number

from dsms.knowledge.semantics.units import (  # isort:skip
    get_conversion_factor,
    get_property_unit,
)

logger = logging.Logger(__name__)

if TYPE_CHECKING:
    from typing import Any, Callable, Dict, List, Optional


class Column(KItemProperty):
    """
    Column of an DataFrame data frame.

    Attributes:
        column_id (int): Column ID in the data frame.
        name (str): Name of the column in the data series.
    """

    column_id: int = Field(..., description="Column ID in the data frame")

    name: str = Field(
        ..., description="Name of the column in the data series."
    )

    def __repr__(self) -> str:
        """Pretty print the numerical datatype"""
        if self.kitem and self.kitem.dsms.config.display_units:
            try:
                unit = f"\tunit={self.get_unit().get('symbol')}\n\t\t"
                string = str(self)
                string = string[:-1] + unit + string[-1:]
            except Exception as error:
                logger.debug(
                    "Could not fetch unit from `%i`: %i", self.name, error.args
                )
                string = str(self)
        else:
            string = str(self)
        return string

    def get(self) -> "List[Any]":
        """
        Download the data for the column in a time series.

        Returns:
            List[Any]: List of data for the column.
        """
        return _get_dataframe_column(self.id, self.column_id)

    def get_unit(self) -> "Dict[str, Any]":
        """
        Retrieve the unit of the column.

        Returns:
            Dict[str, Any]: Dictionary containing unit information.
        """
        return get_property_unit(
            self.id,
            self.name,
            is_dataframe_column=True,
            autocomplete_symbol=self.kitem.dsms.config.autocomplete_units,
        )

    def convert_to(
        self,
        unit_symbol_or_iri: str,
        decimals: "Optional[int]" = None,
        use_input_iri: bool = True,
    ) -> "List[Any]":
        """
        Convert the data of the column to a different unit.

        Args:
            unit_symbol_or_iri (str): Symbol or IRI of the unit to convert to.
            decimals (Optional[int]): Number of decimals to round the result to. Defaults to None.
            use_input_iri (bool): If True, use IRI for unit comparison. Defaults to False.

        Returns:
            List[Any]: List of converted data.
        """
        unit = self.get_unit()
        if use_input_iri:
            input_str = unit.get("iri")
        else:
            input_str = unit.get("symbol")
        factor = get_conversion_factor(
            input_str, unit_symbol_or_iri, decimals=decimals
        )
        data = self.get()
        return [
            number * factor if _is_number(number) else number
            for number in data
        ]


class DataFrameContainer(KItemPropertyList):
    """DataFrame container of a data frame related to a KItem"""

    # OVERRIDE
    @property
    def k_property_item(cls) -> "Callable":
        return Column

    # OVERRIDE
    @property
    def k_property_helper(cls) -> None:
        """Not defined for DataFrame"""

    def to_df(self) -> pd.DataFrame:
        """Return dataframe as pandas DataFrame"""
        data = {column.name: column.get() for column in self}
        return pd.DataFrame.from_dict(data)

    def get(self, name: str) -> "Optional[Column]":
        """Get a column with a certain name."""
        response = None
        for column in self:
            if column.name == name:
                response = column
        return response

    def __getattr__(self, key):
        """Return column as attribute."""
        attribute = self.get(key)
        if not attribute:
            raise AttributeError(f"{self} has no attribute '{key}'")
        return attribute
