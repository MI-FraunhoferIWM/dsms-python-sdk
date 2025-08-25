"""Compacted Knowledge Item implementation of the DSMS"""

from enum import Enum
from typing import Optional, Union
from uuid import UUID, uuid4

from pydantic import (  # isort: skip
    BaseModel,
    ConfigDict,
    Field,
    ValidationInfo,
    field_validator,
    field_serializer,
)

from dsms.core.session import Session  # isort: skip
from dsms.knowledge.ktype import KType  # isort: skip
from dsms.knowledge.utils import _slugify, print_model  # isort: skip


class KItemBaseModel(BaseModel):
    """Basic data model for a KItem"""

    id: Optional[UUID] = Field(
        default_factory=uuid4,
        description="ID of the KItem",
    )


class KItemCompactedModel(KItemBaseModel):
    """
    KItem compacted model for the search-endpoint."""

    name: str = Field(
        ..., description="Human readable name of the KItem", max_length=300
    )
    ktype_id: Union[Enum, str] = Field(..., description="Type ID of the KItem")
    ktype: Optional[Union[Enum, KType]] = Field(
        None, description="KType of the KItem", exclude=True
    )
    slug: Optional[str] = Field(
        None,
        description="Slug of the KItem",
        min_length=4,
        max_length=1000,
    )

    def __str__(self) -> str:
        """Pretty print the kitem fields"""
        return print_model(self, "kitem")

    def __repr__(self) -> str:
        """Pretty print the kitem Fields"""
        return str(self)

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, value: str, info: ValidationInfo) -> str:
        """Validate slug"""

        kitem_id = info.data["id"]
        name = info.data["name"]

        if not value:
            value = _slugify(name)
            if len(value) < 4:
                raise ValueError(
                    "Slug length must have a minimum length of 4."
                )
            if Session.dsms.config.individual_slugs:
                value += f"-{str(kitem_id).split('-', maxsplit=1)[0]}"
        return value

    @field_validator("ktype_id")
    @classmethod
    def validate_ktype_id(cls, value: Union[str, Enum]) -> KType:
        """Validate the ktype id of the KItem"""

        if isinstance(value, str):
            ktype = Session.ktypes.get(value)
            if not ktype:
                raise TypeError(
                    f"KType for `ktype_id={value}` does not exist."
                )
            value = ktype
        if not hasattr(value, "id"):
            raise TypeError(
                "Not a valid KType. Provided Enum does not have an `id`."
            )

        return value.id

    @field_validator("ktype")
    @classmethod
    def validate_ktype(
        cls, value: Optional[Union[KType, Enum]], info: ValidationInfo
    ) -> KType:
        """Validate the ktype of the KItem"""

        ktype_id = info.data.get("ktype_id")

        if not value:
            value = Session.ktypes.get(ktype_id)
            if not value:
                raise TypeError(
                    f"KType for `ktype_id={ktype_id}` does not exist."
                )
        if not hasattr(value, "id"):
            raise TypeError(
                "Not a valid KType. Provided Enum does not have an `id`."
            )

        if value.id != ktype_id:
            raise TypeError(
                f"KType for `ktype_id={ktype_id}` does not match "
                f"the provided `ktype`."
            )

        return value

    @field_serializer("id")
    def serialize_id(self, value: Union[str, UUID]) -> str:
        """Serialize KItem ID"""
        return str(value)

    model_config = ConfigDict(
        validate_assignment=True,
        validate_default=True,
        exclude={"ktype", "avatar"},
        arbitrary_types_allowed=True,
    )
