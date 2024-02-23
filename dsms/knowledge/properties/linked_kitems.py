"""Linked KItems KProperty"""


from typing import TYPE_CHECKING, Optional
from uuid import UUID

from pydantic import ConfigDict, Field, model_serializer

from dsms.knowledge.properties.base import KProperty, KPropertyItem
from dsms.knowledge.utils import _get_kitem

if TYPE_CHECKING:
    from typing import Any, Callable, Dict, Union

    from dsms import KItem


class LinkedKItem(KPropertyItem):
    """Data model of a linked KItem"""

    # OVERRIDE
    id: Optional[UUID] = Field(
        None,
        description="ID of the KItem to be linked",
    )
    source_id: Optional[UUID] = Field(
        None, description="Source ID of the KItem"
    )

    # OVERRIDE
    model_config = ConfigDict(exclude={})

    # OVERRIDE
    def __setattr__(self, index: int, item: "Any") -> None:
        """Add KItem to updated buffer."""
        if self._kitem and self.source_id not in self.context.buffers.updated:
            self.context.buffers.updated.update({self.source_id: self._kitem})
        super().__setattr__(index, item)

    # OVERRIDE
    @property
    def kitem(cls) -> "KItem":
        """KItem related to the KPropertyItem"""
        if not cls.id:
            raise ValueError("KItem not defined yet for KProperty")
        return _get_kitem(cls.source_id)

    # OVERRIDE
    @model_serializer
    def serialize(self):
        """Serialize KPropertItem"""
        return {key: str(value) for key, value in self.__dict__.items()}


class LinkedKItemsProperty(KProperty):
    """KProperty for linked KItems"""

    # OVERRIDE
    @property
    def k_property_item(cls) -> "Callable":
        return LinkedKItem

    # OVERRIDE
    def _add(self, item: LinkedKItem) -> LinkedKItem:
        """Side effect when an LinkedKItem is added to the KProperty"""
        if self.kitem:
            item = self.k_property_item(id=item.id, source_id=self.kitem.id)
        else:
            item = self.k_property_item(id=item.id)
        return item

    # OVERRIDE
    def _update(self, item: LinkedKItem) -> LinkedKItem:
        """Side effect when an LinkedKItem is updated at the KProperty"""
        return item

    # OVERRIDE
    def _get(self, item: LinkedKItem) -> LinkedKItem:
        """Side effect when getting the LinkedKItem for a specfic kitem"""
        return _get_kitem(item.id)

    # OVERRIDE
    def _delete(self, item: LinkedKItem) -> None:
        """Side effect when deleting the LinkedKItem of a KItem"""

    # OVERRIDE
    def __setitem__(
        self, index: int, item: "Union[Dict, KPropertyItem]"
    ) -> None:
        """Add or Update KPropertyItem and add it to the updated-buffer."""

        self._mark_as_updated()
        item = self._check_k_property_item(item)
        if self.kitem:
            item.source_id = self.kitem.id
        try:
            if self[index] != item:
                item = self._update(item)
        except IndexError:
            item = self._add(item)
        super().super().__setitem__(index, item)  # pylint: disable=no-member

    # OVERRIDE
    def _check_and_add_item(self, item: "Union[Dict, Any]") -> KPropertyItem:
        item = self._check_k_property_item(item)
        if self.kitem:
            item.source_id = self.kitem.id
        return self._add(item)

    # OVERRIDE
    @property
    def kitem(cls) -> "KItem":
        """KItem context of the field"""
        return cls._kitem

    # OVERRIDE
    @kitem.setter
    def kitem(cls, value: "KItem") -> None:
        """KItem setter"""
        cls._kitem = value
        for item in cls:
            item.source_id = cls.kitem.id
