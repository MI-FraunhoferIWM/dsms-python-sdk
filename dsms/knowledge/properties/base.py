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
from dsms.knowledge.utils import _get_kitem  # isort:skip


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
        values = ", ".join(
            [
                f"{key}={value}"
                for key, value in self.__dict__.items()
                if key not in self.exclude
            ]
        )
        return f"{self.__class__.__name__}({values})"

    def __repr__(self) -> str:
        """Pretty print the KProperty"""
        return str(self)

    def __setattr__(self, index: int, item: "Any") -> None:
        """Add KItem to updated buffer."""
        if self._kitem and self.id not in self.context.buffers.updated:
            self.context.buffers.updated.update({self.id: self._kitem})
        super().__setattr__(index, item)

    def __hash__(self) -> int:
        return hash(str(self))

    @property
    def kitem(cls) -> "KItem":
        """KItem related to the KPropertyItem"""
        if not cls.id:
            raise ValueError("KItem not defined yet for KProperty")
        return _get_kitem(cls.id)

    @property
    def exclude(cls) -> "Optional[Set[str]]":
        """Fields to be excluded from the JSON-schema"""
        return cls.model_config.get("exclude")

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

    @abstractmethod
    def _add(self, item: KPropertyItem) -> KPropertyItem:
        """Side effect when an KPropertyItem is added to the KProperty"""

    @abstractmethod
    def _update(self, item: KPropertyItem) -> KPropertyItem:
        """Side effect when an KPropertyItem is updated in the KProperty"""

    @abstractmethod
    def _get(self, item: KPropertyItem) -> KPropertyItem:
        """Side effect when an KPropertyItem is retrieved from the KProperty"""

    @abstractmethod
    def _delete(self, item: KPropertyItem) -> None:
        """Side effect when an KPropertyItem is deleted from the KProperty"""

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
        item = self._check_k_property_item(item)
        if self.kitem:
            item.id = self.kitem.id
        try:
            if self[index] != item:
                item = self._update(item)
        except IndexError:
            item = self._add(item)
        super().__setitem__(index, item)

    def __delitem__(self, index: int) -> None:
        """Delete the KPropertyItem from the KProperty"""

        self._mark_as_updated()
        item = super().__delitem__(index)
        self._delete(item)

    def __getitem__(self, index: int) -> KPropertyItem:
        """Get the KPropertyItem from the KProperty"""

        item = super().__getitem__(index)
        return self._get(item)

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
                    item = self._check_and_add_item(subitem)
                    to_extend.append(item)
            elif isinstance(item, (dict, KPropertyItem, KItem)):
                item = self._check_and_add_item(item)
                to_extend.append(item)
            else:
                to_extend.append(item)
        self._mark_as_updated()
        super().extend(to_extend)

    def append(self, item: "Union[Dict, Any]") -> None:
        """Append KPropertyItem to KProperty"""

        item = self._check_and_add_item(item)
        self._mark_as_updated()
        super().append(item)

    def insert(self, index: int, item: "Union[Dict, Any]") -> None:
        """Insert KPropertyItem at KProperty at certain index"""

        item = self._check_and_add_item(item)
        self._mark_as_updated()
        super().insert(index, item)

    def pop(self, index=-1) -> KPropertyItem:
        """Pop KPropertyItem from KProperty"""

        item = super().pop(index)
        self._mark_as_updated()
        self._delete(item)
        return item

    def remove(self, item: "Union[Dict, Any]") -> None:
        """Remove KPropertyItem from KProperty"""

        self._mark_as_updated()
        self._delete(item)
        super().remove(item)

    def _check_and_add_item(self, item: "Union[Dict, Any]") -> KPropertyItem:
        item = self._check_k_property_item(item)
        if self.kitem:
            item.id = self.kitem.id
        return self._add(item)

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
            item.id = cls.kitem.id

    @property
    def values(cls) -> "List[Dict[str, Any]]":
        """Values of the KProperty"""
        return list(cls)
