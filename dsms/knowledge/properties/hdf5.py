"""HDF5 Properties of a KItem"""
from typing import TYPE_CHECKING

import pandas as pd
from pydantic import Field

from dsms.knowledge.properties.base import KProperty, KPropertyItem
from dsms.knowledge.utils import _get_hdf5_column

if TYPE_CHECKING:
    from typing import Any, Callable, List


class Column(KPropertyItem):
    """Column of an HDF5 data frame"""

    column_id: int = Field(..., description="Column ID in the data frame")

    name: str = Field(
        ..., description="Name of the column in the data series."
    )

    def get(self) -> "List[Any]":
        """Download the data for the column in a time series"""
        return _get_hdf5_column(self.id, self.column_id)


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
