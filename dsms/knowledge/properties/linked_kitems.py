"""Linked KItems of a KItem"""

from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from dsms.core.session import Session
from dsms.core.utils import _name_to_camel
from dsms.knowledge.compacted import KItemCompactedModel
from dsms.knowledge.utils import _get_kitem, print_model

if TYPE_CHECKING:
    from dsms import KItem, KType


class LinkedLinkedKItem(BaseModel):
    """Linked KItem of linked KItems"""

    id: str = Field(..., description="ID of a linked KItem of a linked KItem")

    def __str__(self) -> str:
        """Pretty print the linked KItems of the linked KItem"""
        return print_model(self, "linked_kitem")

    def __repr__(self) -> str:
        """Pretty print the linked KItems of the linked KItem"""
        return str(self)


class KItemRelationshipModel(BaseModel):

    """Data model for a relation between two linked KItems"""

    is_incoming: bool = Field(
        False, description="Whether the relation is incoming"
    )
    label: Optional[str] = Field(None, description="Label of the relation")
    kitem: Union[KItemCompactedModel, Any] = Field(
        ..., description="Linked KItem"
    )
    iri: str = Field(
        "http://purl.org/dc/terms/hasPart",
        description="IRI of the linked KItem",
    )

    @field_validator("kitem", mode="after")
    @classmethod
    def validate_kitem(
        cls, value: Union[KItemCompactedModel, "KItem"]
    ) -> KItemCompactedModel:
        """Validate the custom properties of the linked KItem"""

        if isinstance(value, BaseModel):
            value = value.model_dump()
        if not isinstance(value, dict):
            raise TypeError(
                f"Linked KItem does not have a valid type: {type(value)}"
            )
        return KItemCompactedModel(**value)

    def fetch(self) -> "KItem":
        """Fetch remote KItem"""
        if isinstance(self.kitem, KItemCompactedModel):
            item = self.kitem.fetch()  # pylint: disable=no-member
        else:
            item = self.kitem
        return item


class LinkedKItemsList(list):
    """KItemPropertyList for linked KItems"""

    def get(self, kitem_id: "Union[str, UUID]") -> "KItem":
        """Get the kitem with a certain id which is linked to the source KItem."""
        if not str(kitem_id) in [
            str(connection.kitem.id) for connection in self
        ]:
            raise KeyError(f"A KItem with ID `{kitem_id} is not linked.")
        return Session.kitems.get(str(kitem_id)) or _get_kitem(kitem_id)

    @property
    def by_annotation(self) -> "Dict[str, List[KItem]]":
        """Get the kitems grouped by annotation"""
        grouped = {}
        for linked in self:
            for annotation in linked.kitem.annotations:
                if not annotation.iri in grouped:
                    grouped[annotation.iri] = []
                if not linked in grouped[annotation.iri]:
                    grouped[annotation.iri].append(linked)
        return grouped

    @property
    def by_ktype(self) -> "Dict[KType, List[KItem]]":
        """Get the kitems grouped by ktype"""

        grouped = {}
        for linked in self:
            ktype = Session.dsms.ktypes[_name_to_camel(linked.kitem.ktype_id)]
            if not ktype in grouped:
                grouped[ktype] = []
            if not linked in grouped[ktype]:
                grouped[ktype].append(linked.kitem)
        return grouped
