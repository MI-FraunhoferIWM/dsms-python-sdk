"""Basic property for a KItem"""
from abc import abstractmethod
from typing import TYPE_CHECKING, Optional
from uuid import UUID

from pydantic import (  # isort:skip
    BaseModel,
    ConfigDict,
    Field,
    PrivateAttr,
    model_serializer,
)

from dsms.core.utils import _snake_to_camel  # isort:skip


if TYPE_CHECKING:
    from typing import Any, Callable, Dict, Iterable, List, Set, Union

    from dsms import Context, KItem


class KPropertyItem(BaseModel):
    """List item for the KItem-property"""

    id: Optional[UUID] = Field(
        None, description="KItem ID related to the KPropertyItem"
    )

    model_config = ConfigDict(
        exclude={"id"},
        alias_generator=_snake_to_camel,
        populate_by_name=True,
        from_attributes=True,
    )

    _kitem = PrivateAttr(default=None)

    def __str__(self) -> str:
        """Pretty print the KProperty"""
        values = ",\n\t\t\t".join(
            [
                f"{key}: {value}"
                for key, value in self.__dict__.items()
                if key not in self.exclude
            ]
        )
        return f"{{\n\t\t\t{values}\n\t\t}}"

    def __repr__(self) -> str:
        """Pretty print the KProperty"""
        return str(self)

    def __setattr__(self, index: int, item: "Any") -> None:
        """Add KItem to updated buffer."""
        if self.kitem and self.kitem.id not in self.context.buffers.updated:
            self.context.buffers.updated.update({self.id: self.kitem})
        super().__setattr__(index, item)

    def __hash__(self) -> int:
        return hash(str(self))

    @property
    def kitem(cls) -> "KItem":
        """KItem related to the KPropertyItem"""
        return cls._kitem

    @kitem.setter
    def kitem(cls, item: "KItem") -> None:
        """Set KItem related to the KPropertyItem"""
        cls._kitem = item
        cls.id = item.id

    @property
    def exclude(cls) -> "Optional[Set[str]]":
        """Fields to be excluded from the JSON-schema"""
        return cls.model_config.get("exclude")

    @property
    def context(cls) -> "Context":
        """Getter for Context"""
        from dsms import (  # isort:skip
            Context,
        )

        return Context

    @model_serializer
    def serialize(self):
        """Serialize KPropertItem"""
        return {
            key: value for key, value in self.__dict__.items() if key != "id"
        }


class KProperty(list):
    """Basic class for an KItem-property."""

    def __init__(self, *args) -> None:
        self._kitem: "KItem" = None
        self.extend(args)

    @property
    @abstractmethod
    def k_property_item(cls) -> "Callable":
        """Return the KPropertyItem-class for the KProperty"""

    def __str__(self) -> str:
        """Pretty print the KProperty"""
        values = ", \n".join(["\t\t" + repr(value) for value in self])
        if values:
            values = f"\n{values}\n\t"
        return f"[{values}]"

    def __repr__(self) -> str:
        """Pretty print the KProperty"""
        return str(self)

    def __hash__(self) -> int:
        return hash(str(self))

    def __setitem__(
        self, index: int, item: "Union[Dict, KPropertyItem]"
    ) -> None:
        """Add or Update KPropertyItem and add it to the updated-buffer."""

        self._mark_as_updated()
        item = self._check_item(item)
        super().__setitem__(index, item)

    def __delitem__(self, index: int) -> None:
        """Delete the KPropertyItem from the KProperty"""

        self._mark_as_updated()
        super().__delitem__(index)

    def __imul__(self, index: int) -> None:
        """Imul the KPropertyItem"""
        self._mark_as_updated()
        super().__imul__(index)

    def extend(self, iterable: "Iterable") -> None:
        """Extend KProperty with list of KPropertyItem"""
        from dsms import KItem

        to_extend = []
        for item in iterable:
            if isinstance(item, (list, tuple)):
                for subitem in item:
                    item = self._check_item(subitem)
                    if not item in self:
                        to_extend.append(item)
            elif isinstance(item, (dict, KPropertyItem, KItem)):
                item = self._check_item(item)
                if not item in self:
                    to_extend.append(item)
            else:
                if not item in self:
                    to_extend.append(item)
        if to_extend:
            self._mark_as_updated()
            super().extend(to_extend)

    def append(self, item: "Union[Dict, Any]") -> None:
        """Append KPropertyItem to KProperty"""

        item = self._check_item(item)

        if not item in self:
            self._mark_as_updated()
            super().append(item)

    def insert(self, index: int, item: "Union[Dict, Any]") -> None:
        """Insert KPropertyItem at KProperty at certain index"""

        item = self._check_item(item)
        if not item in self:
            self._mark_as_updated()
            super().insert(index, item)

    def pop(self, index=-1) -> KPropertyItem:
        """Pop KPropertyItem from KProperty"""

        item = super().pop(index)
        self._mark_as_updated()
        return item

    def remove(self, item: "Union[Dict, Any]") -> None:
        """Remove KPropertyItem from KProperty"""

        self._mark_as_updated()
        super().remove(item)

    def _check_item(self, item: "Union[Dict, Any]") -> KPropertyItem:
        item = self._check_k_property_item(item)
        if self.kitem:
            item.kitem = self.kitem
        return item

    def _check_k_property_item(
        self, item: "Union[Dict, Any]"
    ) -> KPropertyItem:
        """Check the type of the processsed KPropertyItem"""
        from dsms import KItem

        if not isinstance(item, (self.k_property_item, dict, KItem, str)):
            raise TypeError(
                f"""Item `{item}` must be of type {self.k_property_item}, {KItem}, {str} or {dict},
                not `{type(item)}`."""
            )
        if isinstance(item, dict):
            item = self.k_property_item(**item)
        return item

    def _mark_as_updated(self) -> None:
        """Add KItem of KProperty to updated buffer"""
        if self._kitem and self._kitem.id not in self.context.buffers.updated:
            self.context.buffers.updated.update({self._kitem.id: self._kitem})

    @property
    def context(cls) -> "Context":
        """Getter for Context"""
        from dsms import (  # isort:skip
            Context,
        )

        return Context

    @property
    def kitem(cls) -> "KItem":
        """KItem context of the field"""
        return cls._kitem

    @kitem.setter
    def kitem(cls, value: "KItem") -> None:
        """KItem setter"""
        cls._kitem = value
        for item in cls:
            item.kitem = cls.kitem

    @property
    def values(cls) -> "List[Dict[str, Any]]":
        """Values of the KProperty"""
        return list(cls)
