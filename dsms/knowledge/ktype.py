"""KItem types"""

import logging
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, Optional, Union
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from dsms.knowledge.utils import (
    _create_custom_properties_model,
    _ktype_exists,
    _refresh_ktype
)

from dsms.core.logging import handler

if TYPE_CHECKING:
    from dsms import Context
    from dsms.core.dsms import DSMS

logger = logging.getLogger(__name__)
logger.addHandler(handler)
logger.propagate = False


class KType(BaseModel):
    """Knowledge type of the knowledge item."""

    id: Union[UUID, str] = Field(..., description="ID of the KType.")
    name: Optional[str] = Field(
        None, description="Human readable name of the KType."
    )
    webform: Optional[Any] = Field(None, description="Form data of the KType.")
    json_schema: Optional[Any] = Field(
        None, description="OpenAPI schema of the KType."
    )
    rdf_mapping: Optional[str] = Field(None, description="")
    created_at: Optional[Union[str, datetime]] = Field(
        None, description="Time and date when the KType was created."
    )
    updated_at: Optional[Union[str, datetime]] = Field(
        None, description="Time and date when the KType was updated."
    )

    def __hash__(self) -> int:
        return hash(str(self))

    def __init__(self, **kwargs: "Any") -> None:
        """Initialize the KType"""
        from dsms import DSMS

        logger.debug("Initialize KType with model data: %s", kwargs)

        # set dsms instance if not already done
        if not self.dsms:
            self.dsms = DSMS()

        super().__init__(**kwargs)

        # add ktype to buffer
        if not self.in_backend and self.id not in self.context.buffers.created:
            logger.debug(
                "Marking KTpe with ID `%s` as created and updated during KItem initialization.",
                self.id,
            )
            self.context.buffers.created.update({self.id: self})
            self.context.buffers.updated.update({self.id: self})

        logger.debug("KType initialization successful.")

    @field_validator("webform")
    @classmethod
    def create_model(cls, value: Optional[Dict[str, Any]]) -> Any:
        """Create the datamodel for the ktype"""
        return _create_custom_properties_model(value)


    @property
    def in_backend(self) -> bool:
        """Checks whether the KType already exists"""
        return _ktype_exists(self)


    @property
    def dsms(cls) -> "DSMS":
        """DSMS context getter"""
        return cls.context.dsms

    @dsms.setter
    def dsms(cls, value: "DSMS") -> None:
        """DSMS context setter"""
        cls.context.dsms = value

    @property
    def context(cls) -> "Context":
        """Getter for Context"""
        from dsms import (  # isort:skip
            Context,
        )
        return Context

    def refresh(self) -> None:
        """Refresh the KType"""
        _refresh_ktype(self)
