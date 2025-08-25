"""KItem types"""

import logging
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional, Union
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from dsms.core.logging import handler
from dsms.core.session import Session
from dsms.knowledge.utils import _refresh_ktype, print_ktype, print_model
from dsms.knowledge.webform import BaseWebformModel, Webform

if TYPE_CHECKING:
    from dsms import DSMS


logger = logging.getLogger(__name__)
logger.addHandler(handler)
logger.propagate = False


class KTypeMapping(BaseWebformModel):
    """KType mapping for process schema specification"""

    dst_ktype_id: str = Field(
        ..., description="The ID of the destination K-type"
    )
    relation_iri: str = Field(..., description="The IRI of the relation")
    relation_name: str = Field(..., description="The name of the relation")


class ProcessSchemaSpec(BaseWebformModel):
    """Process schema specification"""

    id: Optional[Union[str, UUID]] = Field(
        None, description="ID of the process schema spec"
    )
    label: str = Field(..., description="The label of the process schema spec")
    is_child: bool = Field(
        False, description="Indicates if it is a child element"
    )
    mappings: List[KTypeMapping] = Field(
        [], description="List of associated KTypeMappings"
    )
    children: List[Optional["ProcessSchemaSpec"]] = Field(
        [], description="Nested child ProcessSchemaSpecs"
    )

    @field_validator("id")
    @classmethod
    def _validate_uuid(cls, value: Union[str, UUID]) -> str:
        return str(value)


class ProcessSchema(BaseModel):
    """Process Schema of the KType"""

    id: Optional[Union[str, UUID]] = Field(
        None, description="ID of the process schema"
    )
    name: str = Field(..., description="Name of the process schema")
    spec: List[ProcessSchemaSpec] = Field(
        ..., description="Schema of the process schema"
    )
    created_at: Optional[datetime] = Field(
        None, description="Time and date when the process schema was created."
    )
    updated_at: Optional[datetime] = Field(
        None, description="Time and date when the process schema was updated."
    )

    def refresh(self) -> None:
        """Refresh the process schema"""
        new = self.session.dsms.process_schemas.get(self.id)
        if not new:
            return
        for key, value in new.model_dump().items():
            logger.debug(
                "Set updated property `%s` for ProcessSchema with id `%s` after commiting: %s",
                key,
                self.id,
                value,
            )
            setattr(self, key, value)

    @property
    def dsms(self) -> "DSMS":
        """DSMS session getter"""
        return self.session.dsms

    @property
    def session(self) -> "Session":
        """Getter for Session"""
        return Session

    def __hash__(self) -> int:
        return hash(str(self))

    def __repr__(self) -> str:
        """Print the KType"""
        return str(self)

    def __str__(self) -> str:
        """Print the KType"""
        return print_model(self, "process_schema")

    @field_validator("id")
    @classmethod
    def _validate_uuid(cls, value: Union[str, UUID]) -> str:
        return str(value)


class WebformSchema(BaseWebformModel):
    """Schema for a webform."""

    id: Union[str, UUID] = Field(..., description="ID of the Webform.")
    name: str = Field(..., description="Name of the Webform.")
    spec: Webform = Field(..., description="Specification of the Webform.")
    created_at: Optional[Union[str, datetime]] = Field(
        None, description="Time and date when the Webform was created."
    )
    updated_at: Optional[Union[str, datetime]] = Field(
        None, description="Time and date when the Webform was updated."
    )

    @field_validator("id")
    @classmethod
    def _validate_uuid(cls, value: Union[str, UUID]) -> str:
        return str(value)


class KType(BaseModel):
    """Knowledge type of the knowledge item."""

    id: Union[UUID, str] = Field(
        ..., description="ID of the KType.", max_length=50
    )
    name: Optional[str] = Field(
        None, description="Human readable name of the KType.", max_length=50
    )
    webform_schema_id: Optional[str] = Field(
        None,
        description="ID of the webform schema that is used to create a form for this KType.",
    )
    webform_schema: Optional[WebformSchema] = Field(
        None, description="Form data of the KType."
    )
    process_schema_id: Optional[str] = Field(
        None,
        description="ID of the process schema that is used to create a form for this KType.",
    )
    process_schema: Optional[ProcessSchema] = Field(
        None, description="Process schema of the KType."
    )
    created_at: Optional[Union[str, datetime]] = Field(
        None, description="Time and date when the KType was created."
    )
    updated_at: Optional[Union[str, datetime]] = Field(
        None, description="Time and date when the KType was updated."
    )

    def __hash__(self) -> int:
        return hash(str(self))

    def __repr__(self) -> str:
        """Print the KType"""
        return str(self)

    def __str__(self) -> str:
        """Print the KType"""
        return print_ktype(self)

    def refresh(self) -> None:
        """Refresh the KType"""
        _refresh_ktype(self)

    @property
    def dsms(self) -> "DSMS":
        """DSMS session getter"""
        return self.session.dsms

    @property
    def session(self) -> "Session":
        """Getter for Session"""
        return Session
