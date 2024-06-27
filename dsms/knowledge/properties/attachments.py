"""Attachment property of a KItem"""

from pathlib import Path
from typing import TYPE_CHECKING

from pydantic import Field

from dsms.knowledge.properties.base import KItemProperty, KItemPropertyList
from dsms.knowledge.properties.utils import _str_to_dict
from dsms.knowledge.utils import _get_attachment

if TYPE_CHECKING:
    from typing import Any, Callable, Dict, Iterable, List, Union


class Attachment(KItemProperty):
    """Attachment uploaded by a  certain user."""

    name: str = Field(..., description="File name of the attachment")

    def download(self, as_bytes: bool = False) -> "Union[str, bytes]":
        """Download attachment file"""
        return _get_attachment(self.id, self.name, as_bytes)


class AttachmentsProperty(KItemPropertyList):
    """KItemPropertyList for managing attachments."""

    # OVERRIDE
    @property
    def k_property_item(cls) -> "Callable":
        return Attachment

    # OVERRIDE
    @property
    def k_property_helper(cls) -> "Callable":
        """Helper for constructing attachment property"""
        return _str_to_dict

    def extend(self, iterable: "Iterable") -> None:
        """Extend KItemPropertyList with list of KItemProperty"""
        from dsms import KItem

        to_extend = []
        for item in iterable:
            if isinstance(item, (list, tuple)):
                for subitem in item:
                    item = self._check_item(subitem)
                    if not Path(item.name).stem in self.by_name:
                        to_extend.append(item)
            elif isinstance(item, (dict, KItemProperty, KItem)):
                item = self._check_item(item)
                if not Path(item.name).stem in self.by_name:
                    to_extend.append(item)
            else:
                if not Path(item.name).stem in self.by_name:
                    to_extend.append(item)
        if to_extend:
            self._mark_as_updated()
            super().extend(to_extend)

    def append(self, item: "Union[Dict, Any]") -> None:
        """Append KItemProperty to KItemPropertyList"""

        item = self._check_item(item)

        if not Path(item.name).stem in self.by_name:
            self._mark_as_updated()
            super().append(item)

    def insert(self, index: int, item: "Union[Dict, Any]") -> None:
        """Insert KItemProperty at KItemPropertyList at certain index"""

        item = self._check_item(item)
        if not Path(item.name).stem in self.by_name:
            self._mark_as_updated()
            super().insert(index, item)

    @property
    def by_name(cls) -> "List[str]":
        "Return list of names of attachments"
        return {
            Path(attachment.name).stem
            + Path(attachment.name).suffix: attachment
            for attachment in cls
        }
