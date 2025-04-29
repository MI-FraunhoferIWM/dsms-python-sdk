"""KItem types"""

import logging
from datetime import datetime
from typing import TYPE_CHECKING, Any, List, Optional, Union
from uuid import UUID

from pydantic import BaseModel, Field, model_serializer

from dsms.core.logging import handler
from dsms.core.session import Session
from dsms.knowledge.utils import _refresh_ktype, print_ktype
from dsms.knowledge.webform import Webform

if TYPE_CHECKING:
    from dsms import DSMS


logger = logging.getLogger(__name__)
logger.addHandler(handler)
logger.propagate = False


class ProcessSchema(BaseModel):
    """Process Schema of the KType"""

    id: Optional[Union[str, UUID]] = Field(
        None, description="ID of the process schema"
    )
    name: str = Field(..., description="Name of the process schema")
    schema: List[Any] = Field(..., description="Schema of the process schema")
    created_at: datetime = Field(
        ..., description="Time and date when the process schema was created."
    )
    updated_at: datetime = Field(
        ..., description="Time and date when the process schema was updated."
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


class KType(BaseModel):
    """Knowledge type of the knowledge item."""

    id: Union[UUID, str] = Field(
        ..., description="ID of the KType.", max_length=50
    )
    name: Optional[str] = Field(
        None, description="Human readable name of the KType.", max_length=50
    )
    webform: Optional[Webform] = Field(
        None, description="Form data of the KType."
    )
    json_schema: Optional[Any] = Field(
        None, description="OpenAPI schema of the KType."
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

    @model_serializer
    def serialize(self):
        """Serialize ktype."""
        return {
            key: (
                value.model_dump(  # pylint: disable=no-member
                    exclude_none=False, by_alias=True
                )
                if key == "webform"
                and value is not None
                and not isinstance(value, dict)
                else value
            )
            for key, value in self.__dict__.items()
        }

    @property
    def dsms(self) -> "DSMS":
        """DSMS session getter"""
        return self.session.dsms

    @property
    def session(self) -> "Session":
        """Getter for Session"""
        return Session
