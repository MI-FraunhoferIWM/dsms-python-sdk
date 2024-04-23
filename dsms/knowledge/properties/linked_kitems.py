"""Linked KItems KProperty"""


from typing import TYPE_CHECKING, Optional
from uuid import UUID

from pydantic import ConfigDict, Field, PrivateAttr, model_serializer

from dsms.knowledge.properties.base import KProperty, KPropertyItem
from dsms.knowledge.utils import _get_kitem

if TYPE_CHECKING:
    from typing import Callable, Union

    from dsms import KItem


def _linked_kitem_helper(kitem: "KItem"):
    from dsms import KItem

    if not isinstance(kitem, KItem):
        raise TypeError(f"{kitem} is not of type {KItem}")
    return {"id": kitem.id}


class LinkedKItem(KPropertyItem):
    """Data model of a linked KItem"""

    # OVERRIDE
    id: Optional[UUID] = Field(
        None,
        description="ID of the KItem to be linked",
    )

    _kitem = PrivateAttr(default=None)

    # OVERRIDE
    model_config = ConfigDict(exclude={})

    # OVERRIDE
    @property
    def kitem(cls) -> "KItem":
        """KItem related to the linked KItem"""
        return cls._kitem

    # OVERRIDE
    @kitem.setter
    def kitem(cls, value: "KItem") -> None:
        """Set KItem related to the linked KItem"""
        cls._kitem = value

    # OVERRIDE
    @model_serializer
    def serialize(self):
        """Serialize KPropertItem"""
        base = {key: str(value) for key, value in self.__dict__.items()}
        base.update(source_id=str(self.kitem.id))
        return base


class LinkedKItemsProperty(KProperty):
    """KProperty for linked KItems"""

    # OVERRIDE
    @property
    def k_property_item(cls) -> "Callable":
        return LinkedKItem

    # OVERRIDE
    @property
    def k_property_helper(cls) -> "Callable":
        """Linked KItem helper function"""
        return _linked_kitem_helper

    def get(self, kitem_id: "Union[str, UUID]") -> "KItem":
        """Get the kitem with a certain id which is linked to the source KItem."""
        if not str(kitem_id) in [str(item.id) for item in self]:
            raise KeyError(f"A KItem with ID `{kitem_id} is not linked.")
        return _get_kitem(kitem_id)
