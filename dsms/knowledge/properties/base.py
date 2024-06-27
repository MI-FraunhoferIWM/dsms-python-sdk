"""Basic property for a KItem"""

import logging
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

from dsms.core.logging import handler  # isort:skip

from dsms.core.utils import _snake_to_camel  # isort:skip

logger = logging.getLogger(__name__)
logger.addHandler(handler)
logger.propagate = False

if TYPE_CHECKING:
    from typing import Any, Callable, Dict, Iterable, List, Set, Union

    from dsms import Context, KItem


class KItemProperty(BaseModel):
    """Property of a KItem"""

    id: Optional[UUID] = Field(
        None, description="KItem ID related to the KItemProperty"
    )

    model_config = ConfigDict(
        exclude={"id"},
        alias_generator=_snake_to_camel,
        populate_by_name=True,
        from_attributes=True,
    )

    _kitem = PrivateAttr(default=None)

    def __str__(self) -> str:
        """Pretty print the KItemProperty"""
        values = ",\n\t\t\t".join(
            [
                f"{key}: {value}"
                for key, value in self.__dict__.items()
                if key not in self.exclude
            ]
        )
        return f"{{\n\t\t\t{values}\n\t\t}}"

    def __repr__(self) -> str:
        """Pretty print the KItemProperty"""
        return str(self)

    def __setattr__(self, key: str, item: "Any") -> None:
        """Add KItem to updated buffer."""
        logger.debug(
            "Setting property with key `%s` on KProperty level: %s.", key, item
        )
        if (
            self.kitem
            and self.kitem.id not in self.context.buffers.updated
            and key not in ["_kitem", "kitem", "id"]
        ):
            self.context.buffers.updated.update({self.id: self.kitem})
            logger.debug(
                "Setting KItem with `%s` as  updated KItemProperty.__setattr__"
            )
        super().__setattr__(key, item)

    def __hash__(self) -> int:
        return hash(str(self))

    @property
    def kitem(cls) -> "KItem":
        """KItem related to the KItemProperty"""
        return cls._kitem

    @kitem.setter
    def kitem(cls, item: "KItem") -> None:
        """Set KItem related to the KItemProperty"""
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
        """Serialize KItemProperty"""
        return {
            key: value for key, value in self.__dict__.items() if key != "id"
        }


class KItemPropertyList(list):
    """List of a specific property belonging to a KItem."""

    def __init__(self, *args) -> None:
        self._kitem: "KItem" = None
        to_extend = self._get_extendables(args)
        self.extend(to_extend)

    @property
    @abstractmethod
    def k_property_item(cls) -> "Callable":
        """Return the KItemProperty-class"""

    @property
    @abstractmethod
    def k_property_helper(cls) -> "Optional[Callable]":
        """Optional helper for transforming a given
        input into the k property item"""

    def __str__(self) -> str:
        """Pretty print the KItemPropertyList"""
        values = ", \n".join(["\t\t" + repr(value) for value in self])
        if values:
            values = f"\n{values}\n\t"
        return f"[{values}]"

    def __repr__(self) -> str:
        """Pretty print the KItemPropertyList"""
        return str(self)

    def __hash__(self) -> int:
        return hash(str(self))

    def __setitem__(
        self, index: int, item: "Union[Dict, KItemPropertyList]"
    ) -> None:
        """Add or Update KItemPropertyList and add it to the updated-buffer."""

        logger.debug(
            "Setting property with index `%s` on KPropertyList level: %s.",
            int,
            item,
        )
        self._mark_as_updated()
        item = self._check_item(item)
        super().__setitem__(index, item)

    def __delitem__(self, index: int) -> None:
        """Delete the KItemPropertyList from the KItemProperty"""

        logger.debug(
            "Deleting property with index `%s` on KPropertyList level", int
        )

        self._mark_as_updated()
        super().__delitem__(index)

    def __imul__(self, index: int) -> None:
        """Imul the KItemPropertyList"""
        self._mark_as_updated()
        super().__imul__(index)

    def _get_extendables(
        self, iterable: "Iterable"
    ) -> "List[KItemPropertyList]":
        from dsms import KItem

        to_extend = []
        for item in iterable:
            if isinstance(item, (list, tuple)):
                for subitem in item:
                    item = self._check_item(subitem)
                    if not item in self:
                        to_extend.append(item)
            elif isinstance(item, (dict, KItemPropertyList, KItem)):
                item = self._check_item(item)
                if not item in self:
                    to_extend.append(item)
            else:
                if not item in self:
                    to_extend.append(item)
        return to_extend

    def extend(self, iterable: "Iterable") -> None:
        """Extend KItemPropertyList with list of KItemProperty"""
        to_extend = self._get_extendables(iterable)

        if to_extend:
            logger.debug("Extending KPropertyList with %s.", to_extend)
            self._mark_as_updated()
            super().extend(to_extend)

    def append(self, item: "Union[Dict, Any]") -> None:
        """Append KItemProperty to KItemPropertyList"""

        item = self._check_item(item)

        if not item in self:
            logger.debug("Extending KPropertyList with %s.", item)
            self._mark_as_updated()
            super().append(item)

    def insert(self, index: int, item: "Union[Dict, Any]") -> None:
        """Insert KItemProperty at KItemPropertyList at certain index"""

        item = self._check_item(item)
        if not item in self:
            logger.debug("Inserting into KPropertyList: %s.", item)
            self._mark_as_updated()
            super().insert(index, item)

    def pop(self, index=-1) -> KItemProperty:
        """Pop KItemProperty from KItemPropertyList"""

        item = super().pop(index)
        self._mark_as_updated()
        logger.debug(
            "Popping KPropertyList with index `%s`:  %s.", index, item
        )
        return item

    def remove(self, item: "Union[Dict, Any]") -> None:
        """Remove KItemProperty from KItemPropertyList"""

        logger.debug("Remove from KPropertyList: %s.", item)

        self._mark_as_updated()
        super().remove(item)

    def _check_item(self, item: "Union[Dict, Any]") -> KItemProperty:
        item = self._check_k_property_item(item)
        if self.kitem:
            item.kitem = self.kitem
        return item

    def _check_k_property_item(
        self, item: "Union[Dict, Any]"
    ) -> KItemProperty:
        """Check the type of the processsed KItemProperty"""
        if not isinstance(item, BaseModel):
            if self.k_property_helper and not isinstance(item, dict):
                item = self.k_property_helper(item)
            elif not self.k_property_helper and not isinstance(item, dict):
                raise TypeError(
                    f"""No `k_propertyhelper` defined for {type(self)}.
                    Hence, item `{item}` must be of type {self.k_property_item},
                    {BaseModel} or {dict}, not `{type(item)}`."""
                )
            item = self.k_property_item(**item)
        return item

    def _mark_as_updated(self) -> None:
        """Add KItem of KItemPropertyList to updated buffer"""
        if self._kitem and self._kitem.id not in self.context.buffers.updated:
            logger.debug(
                "Setting KItem with `%s` as updated on KItemPropertyList level"
            )
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
        """Values of the KItemPropertyList"""
        return list(cls)
