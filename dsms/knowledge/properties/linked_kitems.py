"""Linked KItems of a KItem"""

from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union
from uuid import UUID

import yaml
from pydantic import BaseModel, Field, field_validator

from dsms.core.session import Session
from dsms.core.utils import _name_to_camel
from dsms.knowledge.compacted import KItemCompactedModel
from dsms.knowledge.utils import _get_kitem, print_model

if TYPE_CHECKING:
    from dsms import KItem, KType


class KItemLinkedModel(KItemCompactedModel):
    """KItem Linked Model"""

    def fetch(self) -> "KItem":
        """Fetch the linked KItem"""
        return Session.kitems.get(str(self.id)) or _get_kitem(
            Session.dsms, self.id
        )


class KItemRelationshipModel(BaseModel):

    """Data model for a relation between two linked KItems"""

    is_incoming: bool = Field(
        False,
        description="""Whether the relation is incoming. This field is read-only.
        Link with the field set to `true` are ignored during the commit""",
        frozen=True,
    )
    label: Optional[str] = Field(None, description="Label of the relation")
    kitem: Union[KItemCompactedModel, KItemLinkedModel, Any] = Field(
        ..., description="Linked KItem"
    )
    iri: str = Field(
        "http://purl.org/dc/terms/hasPart",
        description="IRI of the linked KItem",
    )
    generated_by: Optional[str] = Field(
        None,
        description="""Indicates from which field in the custom properties
        section the KItem link was optionally generated from.
        This field is read-only and will not pushed to the backend.""",
    )

    @field_validator("kitem", mode="after")
    @classmethod
    def validate_kitem(
        cls, value: Union[KItemCompactedModel, KItemLinkedModel, "KItem"]
    ) -> KItemLinkedModel:
        """Validate the custom properties of the linked KItem"""

        if isinstance(value, BaseModel):
            value = value.model_dump()
        if not isinstance(value, dict):
            raise TypeError(
                f"Linked KItem does not have a valid type: {type(value)}"
            )
        return KItemLinkedModel(**value)

    def fetch(self) -> "KItem":
        """Fetch remote KItem"""
        if isinstance(self.kitem, KItemCompactedModel):
            item = self.kitem.fetch()  # pylint: disable=no-member
        else:
            item = self.kitem
        return item

    def __str__(self) -> str:
        """Pretty print the relationship fields"""
        return print_model(
            self,
            "relationship",
            exclude_extra=Session.dsms.config.hide_properties,
        )

    def __repr__(self) -> str:
        """Pretty print the relationship Fields"""
        return str(self)


class LinkedKItemsList(list):
    """KItemPropertyList for linked KItems"""

    def get(self, kitem_id: "Union[str, UUID]") -> "KItem":
        """Get the kitem with a certain id which is linked to the source KItem."""
        return self.by_id[str(kitem_id)]

    def __str__(self):
        """Pretty print the LinkedKItemList"""
        from dsms.knowledge.utils import dump_model

        return yaml.dump(
            [
                dump_model(
                    connection,
                    exclude_extra=Session.dsms.config.hide_properties,
                )
                for connection in self
            ]
        )

    def __repr__(self):
        """Pretty print the LinkedKItemList"""
        return str(self)

    @property
    def by_id(self) -> "Dict[str, KItemLinkedModel]":
        """Get the linked kitems by id"""
        return {
            str(connection.kitem.id): connection.kitem for connection in self
        }

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

    @property
    def by_relation(self) -> "Dict[str, List[KItem]]":
        """Get the linked kitems by relation"""
        by_relation = {}
        for connection in self:
            if connection.iri not in by_relation:
                by_relation[connection.iri] = []
            by_relation[connection.iri] += [connection.kitem]
        return by_relation
