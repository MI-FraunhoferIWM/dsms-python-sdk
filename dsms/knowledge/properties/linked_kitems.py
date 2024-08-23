"""Linked KItems of a KItem"""

from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union
from uuid import UUID

from pydantic import (  # isort:skip
    BaseModel,
    ConfigDict,
    Field,
    PrivateAttr,
    model_serializer,
    field_validator,
)

from dsms.core.utils import _name_to_camel  # isort:skip
from dsms.knowledge.properties.base import (  # isort:skip
    KItemProperty,
    KItemPropertyList,
)
from dsms.knowledge.ktype import KType  # isort:skip
from dsms.knowledge.properties.affiliations import Affiliation  # isort:skip
from dsms.knowledge.properties.annotations import Annotation  # isort:skip
from dsms.knowledge.properties.attachments import Attachment  # isort:skip
from dsms.knowledge.properties.authors import Author  # isort:skip
from dsms.knowledge.properties.contacts import ContactInfo  # isort:skip
from dsms.knowledge.properties.external_links import ExternalLink  # isort:skip
from dsms.knowledge.properties.user_groups import UserGroup  # isort:skip
from dsms.knowledge.utils import _get_kitem  # isort:skip


if TYPE_CHECKING:
    from typing import Callable

    from dsms import KItem


def _linked_kitem_helper(kitem: "KItem"):
    from dsms import KItem

    if not isinstance(kitem, KItem):
        raise TypeError(f"{kitem} is not of type {KItem}")
    return {"id": kitem.id}


class LinkedLinkedKItem(BaseModel):
    """Linked KItem of linked KItems"""

    id: str = Field(..., description="ID of a linked KItem of a linked KItem")

    def __str__(self) -> str:
        """Pretty print the linked KItems of the linked KItem"""
        values = ",\n\t\t\t".join(
            [f"{key}: {value}" for key, value in self.__dict__.items()]
        )
        return f"{{\n\t\t\t{values}\n\t\t}}"

    def __repr__(self) -> str:
        """Pretty print the linked KItems of the linked KItem"""
        return str(self)


class LinkedKItemSummary(BaseModel):
    """Summary of a linked KItem"""

    id: str = Field(..., description="ID of the linked KItem")

    text: str = Field(
        ..., description="Text for the summary of the linked KItem"
    )


class LinkedKItem(KItemProperty):
    """Data model of a linked KItem"""

    # OVERRIDE
    id: Optional[UUID] = Field(
        None,
        description="ID of the KItem to be linked",
    )

    name: str = Field(..., description="Name of the linked KItem")

    slug: str = Field(..., description="Slug of the linked KItem")

    ktype_id: str = Field(..., description="Ktype ID of the linked KItem")

    summary: Optional[Union[str, LinkedKItemSummary]] = Field(
        None, description="Summary of the linked KItem."
    )

    avatar_exists: bool = Field(
        False, description="Wether the linked KItem has an avatar."
    )

    annotations: List[Optional[Annotation]] = Field(
        [], description="Annotations of the linked KItem"
    )

    linked_kitems: List[Optional[LinkedLinkedKItem]] = Field(
        [], description="Linked KItems of the linked KItem"
    )

    external_links: List[Optional[ExternalLink]] = Field(
        [], description="External links of the linked KItem"
    )

    contacts: List[Optional[ContactInfo]] = Field(
        [], description="Contact info of the linked KItem"
    )

    authors: List[Optional[Author]] = Field(
        [], description="Authors of the linked KItem"
    )

    linked_affiliations: List[Optional[Affiliation]] = Field(
        [], description="Linked affiliations of the linked KItem"
    )

    attachments: List[Union[str, Optional[Attachment]]] = Field(
        [], description="Attachment of the linked KItem"
    )

    user_groups: List[Optional[UserGroup]] = Field(
        [], description="User groups of the linked KItem"
    )

    custom_properties: Optional[Any] = Field(
        None, description="Custom properies of the linked KItem"
    )

    created_at: Optional[Union[str, datetime]] = Field(
        None, description="Time and date when the KItem was created."
    )
    updated_at: Optional[Union[str, datetime]] = Field(
        None, description="Time and date when the KItem was updated."
    )

    _kitem = PrivateAttr(default=None)

    # OVERRIDE
    model_config = ConfigDict(exclude={}, arbitrary_types_allowed=True)

    def fetch(self) -> "KItem":
        """Fetch the linked KItem"""
        return _get_kitem(self.id)

    def is_a(self, to_be_compared: KType) -> bool:
        """Check the KType of the KItem"""
        return (
            self.ktype_id.value  # pylint: disable=no-member
            == to_be_compared.value
        )

    # OVERRIDE
    def __str__(self) -> str:
        """Pretty print the linked KItem"""
        values = "\n\t\t\t".join(
            [
                f"{key}: {value}"
                for key, value in self.__dict__.items()
                if key not in self.exclude
            ]
        )
        return f"\n\t\t\t{values}\n\t\t"

    # OVERRIDE
    def __repr__(self) -> str:
        """Pretty print the linked KItem"""
        return str(self)

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

    @field_validator("attachments", mode="before")
    @classmethod
    def validate_attachments_before(
        cls, value: List[Union[str, Attachment]]
    ) -> List[Attachment]:
        """Validate attachments Field"""
        return [
            Attachment(name=attachment)
            if isinstance(attachment, str)
            else attachment
            for attachment in value
        ]

    @field_validator("summary", mode="after")
    @classmethod
    def validate_summary_before(
        cls, value: Union[str, LinkedKItemSummary]
    ) -> str:
        """Validate summary Field"""
        if isinstance(value, LinkedKItemSummary):
            value = value.text
        return value

    # OVERRIDE
    @model_serializer
    def serialize_author(self) -> Dict[str, Any]:
        """Serialize linked kitems model"""
        return {
            key: (
                str(value)
                if key in ["updated_at", "created_at", "id"]
                else value
            )
            for key, value in self.__dict__.items()
        }

    @field_validator("custom_properties")
    @classmethod
    def validate_custom_properties(
        cls, value: "Optional[Dict[str, Any]]"
    ) -> "Optional[Dict[str, Any]]":
        """Validate the custom properties of the linked KItem"""
        if value:
            value = value.get("content") or value
        return value


class LinkedKItemsProperty(KItemPropertyList):
    """KItemPropertyList for linked KItems"""

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

    @property
    def by_annotation(self) -> "Dict[str, List[KItem]]":
        """Get the kitems grouped by annotation"""
        grouped = {}
        for linked in self:
            for annotation in linked.annotations:
                if not annotation.iri in grouped:
                    grouped[annotation.iri] = []
                if not linked in grouped[annotation.iri]:
                    grouped[annotation.iri].append(linked)
        return grouped

    @property
    def by_ktype(self) -> "Dict[KType, List[KItem]]":
        """Get the kitems grouped by ktype"""
        from dsms import Context

        grouped = {}
        for linked in self:
            ktype = Context.dsms.ktypes[_name_to_camel(linked.ktype_id)]
            if not ktype in grouped:
                grouped[ktype] = []
            if not linked in grouped[ktype]:
                grouped[ktype].append(linked)
        return grouped
