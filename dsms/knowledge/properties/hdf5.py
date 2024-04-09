"""HDF5 Properties of a KItem"""
from typing import TYPE_CHECKING

import numpy as np
import pandas as pd
from pydantic import Field

from dsms.knowledge.properties.base import KProperty, KPropertyItem
from dsms.knowledge.utils import _get_hdf5_column

from dsms.knowledge.semantics.units import (  # isort:skip
    get_conversion_factor,
    get_property_unit,
)

if TYPE_CHECKING:
    from typing import Any, Callable, Dict, List, Optional


class Column(KPropertyItem):
    """
    Column of an HDF5 data frame.

    Attributes:
        column_id (int): Column ID in the data frame.
        name (str): Name of the column in the data series.
    """

    column_id: int = Field(..., description="Column ID in the data frame")

    name: str = Field(
        ..., description="Name of the column in the data series."
    )

    def get(self) -> "List[Any]":
        """
        Download the data for the column in a time series.

        Returns:
            List[Any]: List of data for the column.
        """
        return _get_hdf5_column(self.id, self.column_id)

    def get_unit(self) -> "Dict[str, Any]":
        """
        Retrieve the unit of the column.

        Returns:
            Dict[str, Any]: Dictionary containing unit information.
        """
        return get_property_unit(self.id, self.name, is_hdf5_column=True)

    def convert_to(
        self,
        unit_symbol_or_iri: str,
        decimals: "Optional[int]" = None,
        use_input_iri: bool = False,
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
        return list(np.array(data) * factor)


class HDF5Container(KProperty):
    """HDF5 container of a data frame related to a KItem"""

    # OVERRIDE
    @property
    def k_property_item(cls) -> "Callable":
        return Column

    # OVERRIDE
    def _add(self, item: Column) -> Column:
        """Side effect when an Column is added to the KProperty"""
        return item

    # OVERRIDE
    def _update(self, item: Column) -> Column:
        """Side effect when an Column is updated at the KProperty"""
        return item

    # OVERRIDE
    def _delete(self, item: Column) -> None:
        """Side effect when deleting the Column of a KItem"""

    # OVERRIDE
    def _get(self, item: Column) -> Column:
        """Side effect when getting the Column for a specfic kitem"""
        return item

    def to_df(self) -> pd.DataFrame:
        """Return hdf5 as pandas DataFrame"""
        data = {column.name: column.get() for column in self}
        return pd.DataFrame.from_dict(data)

    def get(self, name: str) -> "Optional[Column]":
        """Get a column with a certain name."""
        response = None
        for column in self:
            if column.name == name:
                response = column
        return response
