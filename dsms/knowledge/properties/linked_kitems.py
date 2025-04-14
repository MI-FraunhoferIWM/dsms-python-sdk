"""Linked KItems of a KItem"""

from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union
from uuid import UUID

from pydantic import (  # isort:skip
    BaseModel,
    AliasChoices,
    Field,
    model_serializer,
    field_validator,
)

from dsms.core.session import Session  # isort:skip
from dsms.core.utils import _name_to_camel  # isort:skip
from dsms.knowledge.ktype import KType  # isort:skip
from dsms.knowledge.properties.summary import Summary  # isort:skip
from dsms.knowledge.properties.apps import App  # isort:skip
from dsms.knowledge.properties.affiliations import Affiliation  # isort:skip
from dsms.knowledge.properties.annotations import Annotation  # isort:skip
from dsms.knowledge.properties.attachments import Attachment  # isort:skip
from dsms.knowledge.properties.authors import Author  # isort:skip
from dsms.knowledge.properties.contacts import ContactInfo  # isort:skip
from dsms.knowledge.properties.external_links import ExternalLink  # isort:skip
from dsms.knowledge.properties.user_groups import UserGroup  # isort:skip
from dsms.knowledge.utils import _get_kitem, print_model  # isort:skip
from dsms.knowledge.webform import KItemCustomPropertiesModel  # isort:skip


if TYPE_CHECKING:
    from dsms import KItem


class LinkedLinkedKItem(BaseModel):
    """Linked KItem of linked KItems"""

    id: str = Field(..., description="ID of a linked KItem of a linked KItem")

    def __str__(self) -> str:
        """Pretty print the linked KItems of the linked KItem"""
        return print_model(self, "linked_kitem")

    def __repr__(self) -> str:
        """Pretty print the linked KItems of the linked KItem"""
        return str(self)


class LinkedKItem(BaseModel):
    """Data model of a linked KItem"""

    id: UUID = Field(
        ...,
        description="ID of the KItem to be linked",
    )

    name: str = Field(..., description="Name of the linked KItem")

    slug: str = Field(..., description="Slug of the linked KItem")

    ktype_id: str = Field(..., description="Ktype ID of the linked KItem")

    summary: Optional[Union[str, Summary]] = Field(
        None, description="Summary of the linked KItem."
    )

    avatar_exists: Optional[bool] = Field(
        False, description="Wether the linked KItem has an avatar."
    )

    annotations: List[Annotation] = Field(
        [], description="Annotations of the linked KItem"
    )

    linked_kitems: List[LinkedLinkedKItem] = Field(
        [], description="Linked KItems of the linked KItem"
    )

    external_links: List[ExternalLink] = Field(
        [], description="External links of the linked KItem"
    )

    contacts: List[ContactInfo] = Field(
        [], description="Contact info of the linked KItem"
    )

    authors: List[Author] = Field(
        [], description="Authors of the linked KItem"
    )

    affiliations: List[Affiliation] = Field(
        [], description="Linked affiliations of the linked KItem"
    )

    attachments: List[Attachment] = Field(
        [], description="Attachment of the linked KItem"
    )

    user_groups: List[UserGroup] = Field(
        [], description="User groups of the linked KItem"
    )

    custom_properties: Optional[KItemCustomPropertiesModel] = Field(
        None, description="Custom properies of the linked KItem"
    )

    apps: List[App] = Field(
        [],
        description="Apps of the linked KItem",
        alias=AliasChoices("kitem_apps", "apps"),
    )

    created_at: Optional[Union[str, datetime]] = Field(
        None, description="Time and date when the KItem was created."
    )
    updated_at: Optional[Union[str, datetime]] = Field(
        None, description="Time and date when the KItem was updated."
    )

    rdf_exists: Optional[bool] = Field(
        False, description="Wether the linked KItem has an RDF subgraph."
    )

    def fetch(self) -> "KItem":
        """Fetch the linked KItem"""
        return Session.kitems.get(str(self.id)) or _get_kitem(
            Session.dsms, self.id
        )

    def is_a(self, to_be_compared: KType) -> bool:
        """Check the KType of the KItem"""
        return self.ktype_id == to_be_compared.id  # pylint: disable=no-member

    # OVERRIDE
    def __str__(self) -> str:
        """Pretty print the linked KItem"""
        return print_model(self, "linked_kitem")

    # OVERRIDE
    def __repr__(self) -> str:
        """Pretty print the linked KItem"""
        return str(self)

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
    def validate_summary_before(cls, value: Union[str, Summary]) -> str:
        """Validate summary Field"""
        if isinstance(value, Summary):
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

    @field_validator("custom_properties", mode="before")
    @classmethod
    def validate_custom_properties(
        cls, value: "Optional[Dict[str, Any]]"
    ) -> "Optional[Dict[str, Any]]":
        """Validate the custom properties of the linked KItem"""
        if isinstance(value, dict):
            value = value.get("content") or value
            if len(value) == 0:
                value = None
        return value


class LinkedKItemsList(list):
    """KItemPropertyList for linked KItems"""

    def get(self, kitem_id: "Union[str, UUID]") -> "KItem":
        """Get the kitem with a certain id which is linked to the source KItem."""
        if not str(kitem_id) in [str(item.id) for item in self]:
            raise KeyError(f"A KItem with ID `{kitem_id} is not linked.")
        return Session.kitems.get(str(kitem_id)) or _get_kitem(kitem_id)

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

        grouped = {}
        for linked in self:
            ktype = Session.dsms.ktypes[_name_to_camel(linked.ktype_id)]
            if not ktype in grouped:
                grouped[ktype] = []
            if not linked in grouped[ktype]:
                grouped[ktype].append(linked)
        return grouped
