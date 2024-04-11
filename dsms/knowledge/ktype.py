"""KItem types"""

from typing import Any, Dict, Optional, Union
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_serializer

from dsms.knowledge.utils import _create_custom_properties_model


class KType(BaseModel):
    """Knowledge type of the knowledge item."""

    id: Union[UUID, str] = Field(..., description="ID of the KType.")
    name: Optional[str] = Field(
        None, description="Human readable name of the KType."
    )
    webform: Optional[Any] = Field(None, description="Form data of the KItem.")
    json_schema: Optional[Any] = Field(
        None, description="OpenAPI schema of the KItem."
    )

    @field_validator("webform")
    @classmethod
    def create_model(cls, value: Optional[Dict[str, Any]]) -> Any:
        """Create the datamodel for the ktype"""
        return _create_custom_properties_model(value)

    @model_serializer
    def serialize(self):
        """Serialize ktype."""
        return {
            key: (
                value
                if not isinstance(value, BaseModel)
                else value.model_dump_json()
            )
            for key, value in self.items()
        }
