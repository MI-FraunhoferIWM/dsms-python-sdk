"""KItem types"""

import json
import logging
from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional, Union
from uuid import UUID

import yaml
from pydantic import BaseModel, Field, model_serializer

from dsms.core.logging import handler
from dsms.core.session import Session
from dsms.knowledge.data_format import DataFormat
from dsms.knowledge.utils import _refresh_ktype, print_ktype
from dsms.knowledge.webform import Webform

if TYPE_CHECKING:
    from dsms import DSMS


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

    def export(self, data_format: DataFormat) -> Any:
        """Export ktypes to different formats"""

        if data_format == DataFormat.HDF5:
            from dsms.knowledge.knowledge_wrapper import (  # isort:skip
                data_to_dict,
                dict_to_hdf5,
            )

            return dict_to_hdf5(data_to_dict(self))

        if data_format == DataFormat.JSON:
            from dsms.knowledge.knowledge_wrapper import data_to_dict

            return json.dumps(data_to_dict(self))

        if data_format == DataFormat.YAML:
            from dsms.knowledge.knowledge_wrapper import data_to_dict

            return yaml.dump(data_to_dict(self), default_flow_style=False)

        raise ValueError(f"Unsupported data format: {data_format}")

    def import_ktype(data, data_format: DataFormat) -> Any:
        """Import objects in different formats to KType"""

        if data_format == DataFormat.HDF5:
            from dsms.knowledge.knowledge_wrapper import hdf5_to_dict

            return hdf5_to_dict(data)

        if data_format == DataFormat.JSON:
            return json.load(data)

        if data_format == DataFormat.YAML:
            return yaml.safe_load(data)

        raise ValueError(f"Unsupported data format: {data_format}")
