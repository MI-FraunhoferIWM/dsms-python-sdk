"""HDF5 Properties of a KItem"""
from typing import TYPE_CHECKING

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
        return _get_hdf5_column(self.id, self.name)


class HDF5Container(KProperty):
    """HDF5 container of a data frame related to a KItem"""

    # OVERRIDE
    @property
    def k_property_item(cls) -> "Callable":
        return Column

    # OVERRIDE
    def _add(self, item: Column) -> None:
        """Side effect when an Column is added to the KProperty"""
        raise NotImplementedError(
            "Adding columns to an HDF5 container is not supported yet"
        )

    # OVERRIDE
    def _update(self, item: Column) -> None:
        """Side effect when an Column is updated at the KProperty"""
        raise NotImplementedError(
            "Updating columns to an HDF5 container is not supported yet"
        )

    # OVERRIDE
    def _delete(self, item: Column) -> None:
        """Side effect when deleting the Column of a KItem"""
        raise NotImplementedError(
            "Deleting columns to an HDF5 container is not supported yet"
        )

    # OVERRIDE
    def _get(self, item: Column) -> Column:
        """Side effect when getting the Column for a specfic kitem"""
        return item
