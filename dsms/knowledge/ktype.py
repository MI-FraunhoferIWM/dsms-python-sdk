"""KItem types"""

from typing import Any, Dict, Optional, Union
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_serializer

from dsms.knowledge.utils import _parse_model


class KType(BaseModel):
    """Knowledge type of the knowledge item."""

    id: Union[UUID, str] = Field(..., description="ID of the KType.")
    name: Optional[str] = Field(
        None, description="Human readable name of the KType."
    )
    form_data: Optional[Any] = Field(
        None, description="Form data of the KItem."
    )
    data_schema: Optional[Any] = Field(
        None, description="OpenAPI schema of the KItem."
    )

    @field_validator("data_schema")
    @classmethod
    def validate_data_schema(cls, value) -> Dict[str, Any]:
        """Validate the data schema of the ktype"""
        if isinstance(value, dict):
            value = _parse_model(value)
        elif not isinstance(value, BaseModel):
            raise TypeError(f"Invalid type for `data_schema`: {type(value)}")
        return value

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
