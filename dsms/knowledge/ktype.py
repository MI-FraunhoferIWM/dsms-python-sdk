"""KItem types"""

import logging
from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional, Union
from uuid import UUID

from pydantic import BaseModel, Field, model_serializer

from dsms.core.logging import handler
from dsms.knowledge.utils import _ktype_exists, _refresh_ktype, print_ktype
from dsms.knowledge.webform import Webform

if TYPE_CHECKING:
    from dsms import Session
    from dsms.core.dsms import DSMS

logger = logging.getLogger(__name__)
logger.addHandler(handler)
logger.propagate = False


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
        if not self.in_backend and self.id not in self.session.buffers.created:
            logger.debug(
                "Marking KType with ID `%s` as created and updated during KItem initialization.",
                self.id,
            )
            self.session.buffers.created.update({self.id: self})
            self.session.buffers.updated.update({self.id: self})

        logger.debug("KType initialization successful.")

    def __setattr__(self, name, value) -> None:
        """Add ktype to updated-buffer if an attribute is set"""
        super().__setattr__(name, value)

        if name != "custom_properties":
            logger.debug(
                "Setting property with key `%s` on KType level: %s.",
                name,
                value,
            )

            if self.id not in self.session.buffers.updated:
                logger.debug(
                    "Setting KType with ID `%s` as updated during KType.__setattr__",
                    self.id,
                )
                self.session.buffers.updated.update({self.id: self})

    def __repr__(self) -> str:
        """Print the KType"""
        return str(self)

    def __str__(self) -> str:
        """Print the KType"""
        return print_ktype(self)

    @property
    def in_backend(self) -> bool:
        """Checks whether the KType already exists"""
        return _ktype_exists(self)

    @property
    def dsms(self) -> "DSMS":
        """DSMS session getter"""
        return self.session.dsms

    @dsms.setter
    def dsms(self, value: "DSMS") -> None:
        """DSMS session setter"""
        self.session.dsms = value

    @property
    def session(self) -> "Session":
        """Getter for Session"""
        from dsms import (  # isort:skip
            Session,
        )

        return Session

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
